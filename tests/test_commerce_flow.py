import uuid
from datetime import timedelta
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import ChannelPrice, ProductOption, ProductVariant
from commerce.models import Cart, Order, PaymentEvent, Voucher
from commerce.services import (add_item, quote_cart, place_order, simulate_payment,
    transition_order, capture_cash, refund_mock)


class CommerceFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.user = User.objects.create_user('buyer', password='Testing-pass-828!')
        cls.user.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.staff = User.objects.create_user('staff')
        cls.staff.groups.add(Group.objects.get(name='STAFF'))
        cls.admin = User.objects.create_user('admin')
        cls.admin.groups.add(Group.objects.get(name='ADMIN'))
        cls.variant = ProductVariant.objects.get(sku='CF02-STANDARD')

    def setUp(self):
        self.cart = Cart.objects.create(user=self.user)
        add_item(self.cart, self.variant.pk, 4)

    def data(self, **updates):
        values = {'customer_name':'Khách demo', 'phone':'0900000000', 'fulfillment':'PICKUP',
            'payment_method':'MOCK_ONLINE', 'idempotency_key':uuid.uuid4(), 'voucher_code':''}
        values.update(updates)
        return values

    def voucher(self, **updates):
        values = dict(code='NAU10', kind='PERCENT', amount=10, min_subtotal=100000,
            starts_at=timezone.now()-timedelta(days=1), ends_at=timezone.now()+timedelta(days=1))
        values.update(updates)
        return Voucher.objects.create(**values)

    def test_quote_options_sale_and_server_totals(self):
        topping = ProductOption.objects.create(product=self.variant.product, name='Topping demo', kind='TOPPING', price_delta=8000)
        self.cart.items.all().delete()
        add_item(self.cart, self.variant.pk, 2, [topping.pk])
        self.assertEqual(quote_cart(self.cart)['total'], 76000)
        price = ChannelPrice.objects.get(variant=self.variant, channel='WEB')
        price.sale_price, price.sale_starts_at, price.sale_ends_at = 25000, timezone.now()-timedelta(days=1), timezone.now()+timedelta(days=1)
        price.save()
        self.assertEqual(quote_cart(self.cart)['total'], 66000)

    def test_voucher_minimum_cap_expiry_limits_and_stacking(self):
        voucher = self.voucher(cap=5000, max_uses=1)
        self.assertEqual(quote_cart(self.cart, self.user, voucher_code='nau10')['discount'], 5000)
        place_order(self.user, self.cart, self.data(voucher_code='NAU10'))
        add_item(self.cart, self.variant.pk, 4)
        with self.assertRaises(ValidationError):
            quote_cart(self.cart, self.user, voucher_code='NAU10')
        voucher.ends_at = timezone.now()-timedelta(seconds=1)
        voucher.save()
        with self.assertRaises(ValidationError):
            quote_cart(self.cart, self.user, voucher_code='NAU10')

    def test_voucher_below_minimum_and_sale_cannot_stack(self):
        self.voucher()
        self.cart.items.update(quantity=1)
        with self.assertRaises(ValidationError):
            quote_cart(self.cart, self.user, voucher_code='NAU10')
        self.cart.items.update(quantity=4)
        price = ChannelPrice.objects.get(variant=self.variant, channel='WEB')
        price.sale_price, price.sale_starts_at, price.sale_ends_at = 27000, timezone.now()-timedelta(days=1), timezone.now()+timedelta(days=1)
        price.save()
        with self.assertRaises(ValidationError):
            quote_cart(self.cart, self.user, voucher_code='NAU10')

    def test_double_order_service_and_snapshots_ignore_client_price(self):
        data = self.data(total=1, price=1)
        first = place_order(self.user, self.cart, data)
        second = place_order(self.user, self.cart, data)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.total, 120000)
        self.assertEqual(first.items.get().unit_price, 30000)
        self.assertEqual(first.payment.amount, first.total)
        self.assertFalse(self.cart.items.exists())

    def test_invalid_checkout_rolls_back_all_records(self):
        self.variant.is_available = False
        self.variant.save()
        with self.assertRaises(ValidationError):
            place_order(self.user, self.cart, self.data())
        self.assertFalse(Order.objects.exists())
        self.assertEqual(self.cart.items.get().quantity, 4)

    def test_guest_checkout_login_preserves_cart(self):
        response = self.client.get('/checkout/')
        self.assertEqual(response.status_code, 302)
        self.client.post('/cart/add/', {'variant':self.variant.pk, 'quantity':2})
        self.client.post('/accounts/login/', {'username':self.user.username,'password':'Testing-pass-828!','next':'/checkout/'})
        self.assertEqual(self.cart.items.get().quantity, 6)
        self.assertEqual(self.client.get('/checkout/').status_code, 200)

    def test_cart_ownership_quantities_and_post_only(self):
        item = self.cart.items.get()
        self.assertEqual(self.client.post(reverse('cart_update', args=[item.pk]), {'quantity':2}).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/cart/add/').status_code, 405)
        self.client.post(reverse('cart_update', args=[item.pk]), {'quantity':-1})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)
        self.client.post(reverse('cart_update', args=[item.pk]), {'quantity':2})
        self.assertEqual(quote_cart(self.cart)['total'], 60000)

    def test_web_checkout_repeat_post_and_new_checkout_key(self):
        self.client.force_login(self.user)
        response = self.client.get('/checkout/')
        data = self.data(idempotency_key=response.context['form'].initial['idempotency_key'], accept_demo='on', action='place', total=1)
        response = self.client.post('/checkout/', data)
        self.assertEqual(response.status_code, 302)
        self.client.post('/checkout/', data)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.get().total, 120000)
        add_item(self.cart, self.variant.pk, 1)
        new = self.client.get('/checkout/').context['form'].initial['idempotency_key']
        self.assertNotEqual(str(new), str(data['idempotency_key']))

    def test_checkout_redirects_directly_to_payment_and_retry_respects_existing_state(self):
        self.client.force_login(self.user)
        token=self.client.get('/checkout/').context['form'].initial['idempotency_key']
        data=self.data(idempotency_key=token,accept_demo='on',action='place')
        response=self.client.post('/checkout/',data)
        order=Order.objects.get(user=self.user)
        payment_url=reverse('mock_payment',args=[order.payment.token])
        self.assertRedirects(response,payment_url,fetch_redirect_response=False)
        payment_page=self.client.get(payment_url)
        self.assertContains(payment_page,'name="outcome" value="success"')
        self.assertContains(payment_page,'Mô phỏng thanh toán thành công')
        self.assertContains(payment_page,'name="outcome" value="failure"')
        self.assertContains(payment_page,'Mô phỏng thanh toán thất bại')
        self.assertRedirects(self.client.post('/checkout/',data),payment_url,fetch_redirect_response=False)
        simulate_payment(self.user,order.payment.token,True)
        detail=reverse('order_detail',args=[order.public_code])
        self.assertRedirects(self.client.post('/checkout/',data),detail,fetch_redirect_response=False)
        transition_order(self.user,order.public_code,'CANCELLED')
        self.assertRedirects(self.client.post('/checkout/',data),detail,fetch_redirect_response=False)
        self.assertEqual(Order.objects.count(),1)
        self.assertEqual(order.payment.__class__.objects.count(),1)

    def test_mock_failure_retry_success_and_repeated_callback(self):
        order = place_order(self.user, self.cart, self.data(payment_method='MOCK_ONLINE'))
        simulate_payment(self.user, order.payment.token, False)
        order.refresh_from_db()
        self.assertEqual(order.status, 'PENDING_PAYMENT')
        self.assertEqual(order.payment.status, 'FAILED')
        simulate_payment(self.user, order.payment.token, True)
        simulate_payment(self.user, order.payment.token, True)
        order.refresh_from_db()
        self.assertEqual(order.payment.status, 'PAID')
        self.assertEqual(order.status, 'CONFIRMED')
        self.assertEqual(PaymentEvent.objects.filter(payment=order.payment, event_key='mock_success').count(), 1)

    def test_order_and_mock_payment_are_owner_only(self):
        order = place_order(self.user, self.cart, self.data(payment_method='MOCK_ONLINE'))
        other = User.objects.create_user('other')
        other.groups.add(Group.objects.get(name='CUSTOMER'))
        self.client.force_login(other)
        self.assertEqual(self.client.get(reverse('order_detail', args=[order.public_code])).status_code, 404)
        self.assertEqual(self.client.post(reverse('mock_payment', args=[order.payment.token]), {'outcome':'success'}).status_code, 404)
        self.client.force_login(self.user)
        for url in ['/account/orders/', reverse('order_detail',args=[order.public_code]), reverse('mock_payment',args=[order.payment.token]),'/cart/','/promotions/']:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_staff_state_machine_audit_and_cash_not_automatic(self):
        order = place_order(self.user, self.cart, self.data())
        with self.assertRaises(ValidationError):
            transition_order(self.staff, order.public_code, 'COMPLETED')
        simulate_payment(self.user, order.payment.token, True)
        for target in ['PREPARING', 'READY', 'PICKUP_WAITING', 'COMPLETED']:
            transition_order(self.staff, order.public_code, target)
        transition_order(self.staff, order.public_code, 'COMPLETED')
        order.refresh_from_db()
        self.assertEqual(order.history.count(), 6)
        # Retain legacy cash-capture coverage using an explicit historical fixture.
        order.payment.__class__.objects.filter(order=order).update(method='PAY_AT_PICKUP', status='UNPAID')
        capture_cash(self.staff, order.public_code)
        capture_cash(self.staff, order.public_code)
        order.refresh_from_db()
        self.assertEqual(order.payment.status, 'PAID')
        self.assertEqual(order.payment.events.filter(event_key='cash_demo').count(), 1)

    def test_cancel_voucher_release_mock_refund_admin_only(self):
        self.voucher()
        order = place_order(self.user, self.cart, self.data(payment_method='MOCK_ONLINE',voucher_code='NAU10'))
        simulate_payment(self.user, order.payment.token, True)
        transition_order(self.user, order.public_code, 'CANCELLED')
        order.refresh_from_db()
        self.assertFalse(order.redemption.is_active)
        self.assertEqual(order.payment.status, 'REFUND_PENDING')
        with self.assertRaises(PermissionDenied):
            refund_mock(self.staff, order.public_code)
        refund_mock(self.admin, order.public_code)
        refund_mock(self.admin, order.public_code)
        order.refresh_from_db()
        self.assertEqual(order.payment.status, 'REFUNDED')

    def test_customer_cannot_cancel_after_preparing_or_use_staff_routes(self):
        order = place_order(self.user, self.cart, self.data())
        simulate_payment(self.user, order.payment.token, True)
        transition_order(self.staff, order.public_code, 'PREPARING')
        with self.assertRaises(ValidationError):
            transition_order(self.user, order.public_code, 'CANCELLED')
        self.client.force_login(self.user)
        self.assertEqual(self.client.get('/dashboard/orders/').status_code, 403)
        self.assertEqual(self.client.post(reverse('cash',args=[order.public_code])).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/dashboard/orders/').status_code, 200)
        self.assertEqual(self.client.post(reverse('refund',args=[order.public_code])).status_code, 403)

    def test_delivery_and_cash_methods_rejected_without_order(self):
        with self.assertRaises(ValidationError):
            quote_cart(self.cart, self.user, fulfillment='DELIVERY')
        for values in [dict(payment_method='COD'), dict(fulfillment='DELIVERY', payment_method='COD', address='Demo')]:
            with self.assertRaises(ValidationError):
                place_order(self.user, self.cart, self.data(**values))
        self.assertFalse(Order.objects.exists())

    def test_checkout_and_mock_mutations_require_csrf(self):
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.user)
        self.assertEqual(csrf.post('/checkout/', self.data()).status_code, 403)

    def test_empty_cart_pages_render_without_server_error(self):
        self.cart.items.all().delete()
        self.client.force_login(self.user)
        self.assertContains(self.client.get('/checkout/'), 'Giỏ hàng đang trống')
        self.assertContains(self.client.get('/cart/'), 'Giỏ hàng trống')
