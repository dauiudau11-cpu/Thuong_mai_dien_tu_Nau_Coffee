"""Pickup-only policy and transactional customer/staff acceptance on isolated PostgreSQL."""
import io
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from catalog.approved_menu import MENU
from catalog.models import ProductVariant, ChannelPrice
from commerce.forms import CheckoutForm
from commerce.models import Cart, Ingredient, Order, Payment, PaymentEvent, StockMovement, StoreSettings
from commerce.operations import balance, scheduled_slot
from commerce.services import add_item, place_order, quote_cart, simulate_payment, transition_order, refund_mock


def simulate_payment_during_open_hours(user, token, success):
    """Keep payment-flow tests independent from the wall clock and store closing time."""
    paid_at = timezone.make_aware(timezone.datetime(2026, 11, 20, 11, 28))
    with patch('commerce.services.timezone.now', return_value=paid_at):
        return simulate_payment(user, token, success)


def setup_fixture(owner):
    call_command('seed_demo', stdout=io.StringIO())
    owner.buyer = User.objects.create_user('pickup-buyer')
    owner.buyer.groups.add(Group.objects.get(name='CUSTOMER'))
    owner.staff = User.objects.create_user('pickup-staff')
    owner.staff.groups.add(Group.objects.get(name='STAFF'))
    owner.admin = User.objects.create_user('pickup-admin')
    owner.admin.groups.add(Group.objects.get(name='ADMIN'))
    owner.variant = ProductVariant.objects.get(sku='CF02-STANDARD')
    owner.cup = Ingredient.objects.get(sku='DEMO-CUP')


class PickupOnlyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        setup_fixture(cls)

    def setUp(self):
        self.cart = Cart.objects.create(user=self.buyer)
        add_item(self.cart, self.variant.pk, 2)

    def data(self, **kwargs):
        return dict(customer_name='Pickup DEMO', phone='0900000000', fulfillment='PICKUP',
            payment_method='MOCK_ONLINE', idempotency_key=uuid.uuid4(), **kwargs)

    def order(self, paid=False):
        order = place_order(self.buyer, self.cart, self.data())
        if paid:
            simulate_payment_during_open_hours(self.buyer, order.payment.token, True)
            order.refresh_from_db()
        return order

    @override_settings(NAU_STANDARD_MENU_ENABLED=False, NAU_DEMO_DELIVERY_ENABLED=True)
    def test_policy_is_unconditional_even_without_menu_flag(self):
        for fulfillment in ['DELIVERY', 'invalid', '']:
            data = self.data(); data['fulfillment'] = fulfillment
            with self.assertRaises(ValidationError):
                place_order(self.buyer, self.cart, data)
            with self.assertRaises(ValidationError):
                quote_cart(self.cart, fulfillment=fulfillment)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(self.cart.items.get().quantity, 2)
        self.assertFalse(StockMovement.objects.filter(reason='CONSUME').exists())

    def test_non_mock_methods_are_rejected(self):
        for method in ['COD', 'PAY_AT_PICKUP', 'BANK_TRANSFER_DEMO', 'EXTERNAL_DEMO', '']:
            data=self.data(); data['payment_method']=method
            with self.assertRaises(ValidationError):
                place_order(self.buyer, self.cart, data)
        self.assertFalse(Order.objects.exists())

    @override_settings(NAU_DEMO_DELIVERY_ENABLED=True)
    def test_forged_delivery_post_preserves_all_business_records(self):
        self.client.force_login(self.buyer)
        form=self.client.get('/checkout/').context['form']
        payload=self.data(); payload.update(idempotency_key=form.initial['idempotency_key'],
            action='place', accept_demo='on', fulfillment='DELIVERY', address='Địa chỉ demo A')
        self.assertEqual(self.client.post('/checkout/',payload).status_code,200)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Payment.objects.exists())
        self.assertTrue(self.cart.items.exists())

    def test_checkout_has_fixed_choices_and_optional_schedule_but_no_address(self):
        form=CheckoutForm(user=self.buyer)
        self.assertEqual(list(form.fields['fulfillment'].choices),[('PICKUP','Nhận tại quán')])
        self.assertEqual([x[0] for x in form.fields['payment_method'].choices],['MOCK_ONLINE'])
        self.assertNotIn('scheduled_for',form.fields)
        self.assertEqual([value for value,_ in form.fields['scheduled_hour'].choices][1:],
            [f'{value:02d}' for value in range(24)])
        self.assertEqual([value for value,_ in form.fields['scheduled_minute'].choices][1:],
            [f'{value:02d}' for value in range(60)])
        for field in ['address','saved_address']:
            self.assertNotIn(field,form.fields)
        self.client.force_login(self.buyer)
        response=self.client.get('/checkout/')
        self.assertContains(response,'id_scheduled_date')
        self.assertContains(response,'id_scheduled_hour')
        self.assertContains(response,'id_scheduled_minute')
        self.assertNotContains(response,'datetime-local')
        for field in ['id_address','id_saved_address']:
            self.assertNotContains(response,field)

    def test_shipping_zero_and_forged_past_schedule_is_rejected(self):
        StoreSettings.objects.filter(name='DEMO').update(delivery_fee=25000,free_delivery_min=999999999)
        data=self.data(scheduled_for=timezone.now()-timedelta(days=3),shipping=25000,total=1)
        with self.assertRaises(ValidationError):
            place_order(self.buyer,self.cart,data)
        self.assertFalse(Order.objects.exists())

    def test_no_available_slot_rolls_back_without_payment_or_cart_loss(self):
        from datetime import time
        frozen=timezone.localtime().replace(hour=14,minute=30,second=0,microsecond=0)
        StoreSettings.objects.filter(name='DEMO').update(slot_capacity=1,preorder_days=1,
            opens_at=time(15),closes_at=time(15,15))
        for day in [0,1]:
            Order.objects.create(user=self.buyer,customer_name='Full slot fixture',phone='0900000000',
                fulfillment='PICKUP',status='CONFIRMED',subtotal=0,total=0,idempotency_key=uuid.uuid4(),
                scheduled_for=frozen.replace(hour=15,minute=0)+timedelta(days=day))
        with patch('commerce.operations.timezone.localtime',return_value=frozen):
            order=self.order()
        self.assertIsNone(order.scheduled_for)
        self.assertEqual(Order.objects.count(),3)
        self.assertEqual(order.payment.status,'PENDING')

    def test_failed_payment_retry_duplicate_success_and_queue(self):
        order=self.order()
        self.client.force_login(self.staff)
        self.assertNotIn(order,list(self.client.get('/dashboard/orders/').context['page_obj']))
        self.assertEqual(self.client.get('/dashboard/kitchen/').context['columns'][0]['count'],0)
        self.assertEqual(self.client.get('/dashboard/').context['new_orders'],0)

        simulate_payment_during_open_hours(self.buyer,order.payment.token,False)
        order.refresh_from_db()
        self.assertEqual(order.status,'PENDING_PAYMENT')
        self.assertEqual(order.payment.status,'FAILED')
        with self.assertRaises(ValidationError):
            transition_order(self.staff,order.public_code,'PREPARING')
        for _ in range(2): simulate_payment_during_open_hours(self.buyer,order.payment.token,True)
        order.refresh_from_db()
        self.assertEqual(order.status,'CONFIRMED')
        self.assertEqual(order.payment.status,'PAID')
        self.assertIn(order,list(self.client.get('/dashboard/orders/').context['page_obj']))
        self.assertEqual(self.client.get('/dashboard/kitchen/').context['columns'][0]['count'],1)
        self.assertEqual(self.client.get('/dashboard/').context['new_orders'],1)
        self.assertEqual(order.history.filter(to_state='CONFIRMED').count(),1)
        self.assertEqual(PaymentEvent.objects.filter(payment=order.payment,event_key='mock_success').count(),1)
        self.assertEqual(Order.objects.count(),1)
        self.assertFalse(StockMovement.objects.filter(order=order).exists())

    def test_successful_payment_sets_exact_thirty_minute_pickup_time(self):
        from datetime import time
        paid_at=timezone.make_aware(timezone.datetime(2026,11,20,11,28))
        StoreSettings.objects.filter(name='DEMO').update(opens_at=time(7),closes_at=time(22),slot_capacity=10)
        order=self.order()
        self.assertIsNone(order.scheduled_for)
        with patch('commerce.services.timezone.now',return_value=paid_at):
            simulate_payment(self.buyer,order.payment.token,True)
        order.refresh_from_db()
        self.assertEqual(timezone.localtime(order.scheduled_for),timezone.localtime(paid_at)+timedelta(minutes=30))

    def test_same_day_cutoff_accepts_2130_and_auto_pickup_can_pass_closing(self):
        placed_at = timezone.make_aware(timezone.datetime(2026, 11, 20, 21, 30))
        paid_at = placed_at + timedelta(minutes=5)
        with patch('django.utils.timezone.now', return_value=placed_at):
            order = place_order(self.buyer, self.cart, self.data())
        with patch('django.utils.timezone.now', return_value=paid_at):
            simulate_payment(self.buyer, order.payment.token, True)
        order.refresh_from_db()
        self.assertEqual(timezone.localtime(order.scheduled_for), timezone.localtime(paid_at) + timedelta(minutes=30))
        self.assertEqual(timezone.localtime(order.scheduled_for).strftime('%H:%M'), '22:05')

    def test_same_day_cutoff_rejects_2131_without_changing_cart(self):
        placed_at = timezone.make_aware(timezone.datetime(2026, 11, 20, 21, 31))
        with patch('django.utils.timezone.now', return_value=placed_at), self.assertRaisesMessage(
                ValidationError, 'Đơn nhận trong ngày được tiếp nhận đến 21:30.'):
            place_order(self.buyer, self.cart, self.data())
        self.assertFalse(Order.objects.exists())
        self.assertEqual(self.cart.items.get().quantity, 2)

    def test_customer_selected_pickup_range_is_0730_through_2200(self):
        baseline = timezone.make_aware(timezone.datetime(2026, 11, 20, 8, 0))
        day = timezone.localtime(baseline) + timedelta(days=1)
        with patch('django.utils.timezone.now', return_value=baseline):
            for hour, minute in ((7, 30), (22, 0)):
                selected = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                self.assertEqual(scheduled_slot(selected, earliest=baseline, exact_minute=True), selected)
            for hour, minute in ((7, 29), (22, 1)):
                selected = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                with self.assertRaisesMessage(ValidationError,
                        'Thời gian nhận hàng không hợp lệ, vui lòng chọn lại thời gian nhận hàng.'):
                    scheduled_slot(selected, earliest=baseline, exact_minute=True)

    def test_selected_schedule_is_not_invalidated_only_by_payment_after_cutoff(self):
        placed_at = timezone.make_aware(timezone.datetime(2026, 11, 20, 21, 25))
        selected = placed_at.replace(hour=22, minute=0)
        with patch('django.utils.timezone.now', return_value=placed_at):
            order = place_order(self.buyer, self.cart, self.data(
                scheduled_for=selected, menu_started_at=placed_at - timedelta(minutes=35)))
        with patch('django.utils.timezone.now', return_value=placed_at + timedelta(minutes=10)):
            simulate_payment(self.buyer, order.payment.token, True)
        order.refresh_from_db()
        self.assertEqual(timezone.localtime(order.scheduled_for), selected)

    def test_manual_pickup_time_requires_server_menu_baseline(self):
        started=timezone.now()
        with self.assertRaises(ValidationError):
            place_order(self.buyer,self.cart,self.data(scheduled_for=started+timedelta(minutes=30),menu_started_at=started))

    def test_web_pickup_accepts_exact_minutes_and_capacity_uses_internal_bucket(self):
        from datetime import time
        StoreSettings.objects.filter(name='DEMO').update(opens_at=time(7), closes_at=time(23, 59),
            preorder_days=7, slot_capacity=10)
        day = timezone.localtime() + timedelta(days=1)
        for index, minute in enumerate((40, 41, 45, 47)):
            selected = day.replace(hour=19, minute=minute, second=0, microsecond=0)
            if index:
                add_item(self.cart, self.variant.pk, 1)
            order = place_order(self.buyer, self.cart, self.data(scheduled_for=selected,
                menu_started_at=selected-timedelta(minutes=35)))
            self.assertEqual(timezone.localtime(order.scheduled_for), selected)
        StoreSettings.objects.filter(name='DEMO').update(slot_capacity=2)
        add_item(self.cart, self.variant.pk, 1)
        with self.assertRaisesMessage(ValidationError,
                'Thời gian nhận hàng không hợp lệ, vui lòng chọn lại thời gian nhận hàng.'):
            place_order(self.buyer, self.cart, self.data(scheduled_for=day.replace(hour=19, minute=44,
                second=0, microsecond=0), menu_started_at=day.replace(hour=19, minute=9,
                second=0, microsecond=0)))

    def test_web_pickup_rejects_less_than_menu_start_plus_35_minutes(self):
        started = timezone.now()
        with self.assertRaisesMessage(ValidationError,
                'Thời gian nhận hàng không hợp lệ, vui lòng chọn lại thời gian nhận hàng.'):
            place_order(self.buyer, self.cart, self.data(scheduled_for=started+timedelta(minutes=34),
                menu_started_at=started))

    def test_prepare_consumes_once_and_completes_pickup_flow(self):
        order=self.order(paid=True)
        before=balance(self.cup)
        for _ in range(2): transition_order(self.staff,order.public_code,'PREPARING')
        self.assertEqual(balance(self.cup),before-Decimal(2))
        self.assertEqual(StockMovement.objects.filter(order=order,ingredient=self.cup).count(),1)
        with self.assertRaises(ValidationError): transition_order(self.buyer,order.public_code,'CANCELLED')
        for state in ['READY','PICKUP_WAITING','COMPLETED']:
            transition_order(self.staff,order.public_code,state)
        order.refresh_from_db(); self.assertEqual(order.status,'COMPLETED')

    def test_paid_cancel_refund_and_callbacks_are_idempotent(self):
        order=self.order(paid=True)
        for _ in range(2): transition_order(self.buyer,order.public_code,'CANCELLED')
        order.refresh_from_db(); self.assertEqual(order.payment.status,'REFUND_PENDING')
        for _ in range(2): refund_mock(self.admin,order.public_code)
        simulate_payment_during_open_hours(self.buyer,order.payment.token,True)
        order.refresh_from_db()
        self.assertEqual(order.status,'CANCELLED')
        self.assertEqual(order.payment.status,'REFUNDED')
        self.assertEqual(order.payment.events.filter(event_key='mock_refund').count(),1)
        self.assertFalse(StockMovement.objects.filter(order=order).exists())
        self.client.force_login(self.staff)
        self.assertNotIn(order,list(self.client.get('/dashboard/orders/').context['page_obj']))

    def test_unpaid_cancel_has_no_fake_refund(self):
        order=self.order()
        transition_order(self.buyer,order.public_code,'CANCELLED')
        simulate_payment_during_open_hours(self.buyer,order.payment.token,True)
        order.refresh_from_db()
        self.assertEqual(order.status,'CANCELLED')
        self.assertEqual(order.payment.status,'PENDING')
        self.assertFalse(order.payment.events.exists())

    def test_duplicate_order_and_invalid_retry_policy(self):
        data=self.data()
        order=place_order(self.buyer,self.cart,data)
        self.assertEqual(place_order(self.buyer,self.cart,data).pk,order.pk)
        data['fulfillment']='DELIVERY'
        with self.assertRaises(ValidationError): place_order(self.buyer,self.cart,data)
        self.assertEqual(Order.objects.count(),1)

    def test_legacy_delivery_is_readable_without_rewriting(self):
        old=Order.objects.create(user=self.buyer,fulfillment='DELIVERY',address='Legacy fixture',
            customer_name='Legacy',phone='0900000000',subtotal=75000,shipping=25000,total=100000,
            status='DELIVERING',idempotency_key=uuid.uuid4(),bill_issued_at=timezone.now())
        Payment.objects.create(order=old,method='BANK_TRANSFER_DEMO',status='PAID',amount=100000)
        before=Order.objects.filter(pk=old.pk).values().get()
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(f'/account/orders/{old.public_code}/').status_code,200)
        self.assertEqual(Order.objects.filter(pk=old.pk).values().get(),before)

    def test_partner_links_are_exact_public_safe_and_read_only(self):
        before=(Order.objects.count(),Payment.objects.count(),StockMovement.objects.count())
        response=self.client.get('/delivery-partners/')
        self.assertContains(response,'Đặt giao tận nơi qua đối tác')
        self.assertEqual(response.content.decode().count('aria-label="Truy cập nền tảng'),3)
        for url in ['https://food.grab.com/vn/vi/','https://shopeefood.vn/','https://food.be.com.vn/']:
            self.assertContains(response,'href="'+url+'" target="_blank" rel="noopener noreferrer"')
        self.assertEqual(before,(Order.objects.count(),Payment.objects.count(),StockMovement.objects.count()))
        self.assertContains(self.client.get('/policies/shipping/'),'Website chỉ nhận',status_code=200)


class PickupRaceTests(TransactionTestCase):
    def setUp(self):
        setup_fixture(self)
        self.cart=Cart.objects.create(user=self.buyer)
        add_item(self.cart,self.variant.pk,2)
        self.order=place_order(self.buyer,self.cart,dict(customer_name='Race',phone='0900000000',
            fulfillment='PICKUP',payment_method='MOCK_ONLINE',idempotency_key=uuid.uuid4()))
        simulate_payment_during_open_hours(self.buyer,self.order.payment.token,True)

    def test_cancel_races_prepare_and_stock_matches_winner(self):
        barrier=Barrier(2)
        def worker(index):
            try:
                barrier.wait(timeout=10)
                try:
                    transition_order(self.staff if index else self.buyer,self.order.public_code,
                        'PREPARING' if index else 'CANCELLED')
                    return 'ok'
                except ValidationError: return 'rejected'
            finally: connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool: result=list(pool.map(worker,[0,1]))
        self.assertCountEqual(result,['ok','rejected'])
        self.order.refresh_from_db()
        movements=StockMovement.objects.filter(order=self.order)
        if self.order.status=='CANCELLED':
            self.assertFalse(movements.exists())
            self.assertEqual(self.order.payment.status,'REFUND_PENDING')
        else:
            self.assertEqual(self.order.status,'PREPARING')
            self.assertTrue(movements.exists())
            self.assertEqual(self.order.payment.status,'PAID')


class PickupPaymentTransactionTests(TransactionTestCase):
    """Exercise the real payment view without TestCase's enclosing transaction."""
    def setUp(self):
        setup_fixture(self)
        self.cart = Cart.objects.create(user=self.buyer)
        add_item(self.cart, self.variant.pk, 1)
        self.order = place_order(self.buyer, self.cart, dict(customer_name='Payment transaction',
            phone='0900000000', fulfillment='PICKUP', payment_method='MOCK_ONLINE',
            idempotency_key=uuid.uuid4()))
        self.client.force_login(self.buyer)

    def test_payment_view_locks_inside_atomic_and_preserves_exact_minute(self):
        from datetime import time
        StoreSettings.objects.filter(name='DEMO').update(opens_at=time(7), closes_at=time(23, 59),
            preorder_days=7, slot_capacity=10)
        selected = (timezone.localtime()+timedelta(days=1)).replace(hour=19, minute=41,
            second=0, microsecond=0)
        response = self.client.post(f'/payments/mock/{self.order.payment.token}/', {
            'outcome':'success', 'scheduled_date':selected.strftime('%Y-%m-%d'),
            'scheduled_hour':'19', 'scheduled_minute':'41'})
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'CONFIRMED')
        self.assertEqual(self.order.payment.status, 'PAID')
        self.assertEqual(timezone.localtime(self.order.scheduled_for), selected)

    def test_invalid_reselection_rolls_back_payment_and_event(self):
        selected = timezone.localtime()+timedelta(minutes=1)
        response = self.client.post(f'/payments/mock/{self.order.payment.token}/', {
            'outcome':'success', 'scheduled_date':selected.strftime('%Y-%m-%d'),
            'scheduled_hour':f'{selected.hour:02d}', 'scheduled_minute':f'{selected.minute:02d}'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
            'Thời gian nhận hàng không hợp lệ, vui lòng chọn lại thời gian nhận hàng.')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PENDING_PAYMENT')
        self.assertEqual(self.order.payment.status, 'PENDING')
        self.assertFalse(PaymentEvent.objects.filter(payment=self.order.payment).exists())
