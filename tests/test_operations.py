from commerce.services import simulate_payment
from datetime import timedelta
from decimal import Decimal
import uuid
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.test import TestCase
from django.utils import timezone
from catalog.models import ProductVariant
from commerce.models import Cart, Order, StoreSettings, Ingredient, StockMovement, LoyaltyLedger
from commerce.services import add_item, place_order, transition_order, capture_cash
from commerce.operations import (balance, adjust_stock, scheduled_slot, verify_delivery, manual_order, reconcile_external)


class OperationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.buyer = User.objects.create_user('ops-buyer')
        cls.buyer.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.staff = User.objects.create_user('ops-staff')
        cls.staff.groups.add(Group.objects.get(name='STAFF'))
        cls.admin = User.objects.create_user('ops-admin', is_staff=True)
        cls.admin.groups.add(Group.objects.get(name='ADMIN'))
        cls.variant = ProductVariant.objects.get(sku='CF02-STANDARD')

    def order(self, qty=2, **updates):
        cart, _ = Cart.objects.get_or_create(user=self.buyer)
        add_item(cart, self.variant.pk, qty)
        data = {'customer_name': 'DEMO', 'phone': '0900000000', 'fulfillment': 'PICKUP',
            'payment_method': 'MOCK_ONLINE', 'idempotency_key': uuid.uuid4(), **updates}
        order = place_order(self.buyer, cart, data)
        simulate_payment(self.buyer, order.payment.token, True)
        order.refresh_from_db()
        return order

    def complete(self, order):
        for state in ['PREPARING', 'READY', 'PICKUP_WAITING', 'COMPLETED']:
            transition_order(self.staff, order.public_code, state)

    def test_inventory_two_cups_exactly_once(self):
        order = self.order()
        cup = Ingredient.objects.get(sku='DEMO-CUP')
        before = balance(cup)
        simulate_payment(self.buyer, order.payment.token, True)
        transition_order(self.staff, order.public_code, 'PREPARING')
        simulate_payment(self.buyer, order.payment.token, True)
        transition_order(self.staff, order.public_code, 'PREPARING')
        self.assertEqual(balance(cup), before - 2)
        self.assertEqual(StockMovement.objects.filter(order=order, ingredient=cup).count(), 1)

    def test_insufficient_stock_rolls_back_all_and_status(self):
        order = self.order()
        cup = Ingredient.objects.get(sku='DEMO-CUP')
        adjust_stock(self.admin, cup.pk, -balance(cup), 'Test hết kho', uuid.uuid4())
        with self.assertRaises(ValidationError):
            simulate_payment(self.buyer, order.payment.token, True)
            transition_order(self.staff, order.public_code, 'PREPARING')
        order.refresh_from_db()
        self.assertEqual(order.status, 'CONFIRMED')
        self.assertFalse(StockMovement.objects.filter(order=order).exists())

    def test_cancellation_does_not_consume_and_cannot_cancel_preparing(self):
        order = self.order()
        transition_order(self.buyer, order.public_code, 'CANCELLED')
        self.assertFalse(StockMovement.objects.filter(order=order).exists())
        other = self.order()
        simulate_payment(self.buyer, other.payment.token, True)
        transition_order(self.staff, other.public_code, 'PREPARING')
        with self.assertRaises(ValidationError):
            transition_order(self.buyer, other.public_code, 'CANCELLED')

    def test_stock_permissions_idempotency_and_negative_guard(self):
        cup = Ingredient.objects.get(sku='DEMO-CUP')
        with self.assertRaises(PermissionDenied):
            adjust_stock(self.staff, cup.pk, Decimal(1), 'Test', uuid.uuid4())
        key = uuid.uuid4()
        first = adjust_stock(self.admin, cup.pk, Decimal(10), 'Nhập thử', key, 'PURCHASE')
        self.assertEqual(first.pk, adjust_stock(self.admin, cup.pk, Decimal(10), 'Nhập thử', key, 'PURCHASE').pk)
        with self.assertRaises(ValidationError):
            adjust_stock(self.admin, cup.pk, -balance(cup)-1, 'Không hợp lệ', uuid.uuid4())

    def test_loyalty_requires_completion_and_payment_and_is_once(self):
        order = self.order()
        order.payment.__class__.objects.filter(order=order).update(method='PAY_AT_PICKUP', status='UNPAID')
        self.complete(order)
        self.assertFalse(LoyaltyLedger.objects.exists())
        capture_cash(self.staff, order.public_code)
        capture_cash(self.staff, order.public_code)
        self.assertEqual(LoyaltyLedger.objects.get().delta, 6)
        self.assertEqual(LoyaltyLedger.objects.count(), 1)

    def test_paid_first_earns_at_completion_and_own_ledger(self):
        order = self.order()
        order.payment.__class__.objects.filter(order=order).update(method='PAY_AT_PICKUP', status='UNPAID')
        capture_cash(self.staff, order.public_code)
        self.assertFalse(LoyaltyLedger.objects.exists())
        self.complete(order)
        self.assertEqual(LoyaltyLedger.objects.get().delta, 6)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/account/loyalty/').context['balance'], 0)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get('/account/loyalty/').context['balance'], 6)

    def test_scheduling_hours_lead_horizon_alignment_and_capacity(self):
        with transaction.atomic():
            slot = scheduled_slot()
            self.assertEqual(slot.minute % 15, 0)
            self.assertTrue(7 <= slot.hour < 22)
            config = StoreSettings.objects.get(name='DEMO')
            config.slot_capacity = 1
            config.save()
        self.order(scheduled_for=slot, menu_started_at=slot-timedelta(minutes=35))
        for invalid in [slot, timezone.now()-timedelta(days=1), slot.replace(hour=23), slot+timedelta(days=9), slot+timedelta(minutes=1)]:
            with self.assertRaises(ValidationError), transaction.atomic():
                scheduled_slot(invalid)

    def test_delivery_confirmation_distance_permission_and_audit(self):
        order = self.order()
        # Historical delivery fixture; current checkout cannot create this.
        Order.objects.filter(pk=order.pk).update(fulfillment='DELIVERY', address='Legacy fixture')
        order.refresh_from_db()
        with self.assertRaises(ValidationError):
            simulate_payment(self.buyer, order.payment.token, True)
            transition_order(self.staff, order.public_code, 'PREPARING')
        with self.assertRaises(PermissionDenied):
            verify_delivery(self.buyer, order.public_code, Decimal('2.5'), 'Demo xác minh')
        with self.assertRaises(ValidationError):
            verify_delivery(self.staff, order.public_code, Decimal('3.1'), 'Ngoài vùng')
        verify_delivery(self.staff, order.public_code, Decimal('2.5'), 'Xác minh thủ công DEMO')
        self.assertTrue(order.history.filter(reason__contains='2.5 km').exists())
        simulate_payment(self.buyer, order.payment.token, True)
        transition_order(self.staff, order.public_code, 'PREPARING')

    def manual(self, **updates):
        data = {'channel': 'APP', 'customer_name': 'DEMO', 'external_reference': 'APP-DEMO-1',
            'idempotency_key': uuid.uuid4(), **updates}
        return manual_order(self.staff, data, [{'variant': self.variant, 'quantity': 2}]), data

    def test_manual_channel_price_reference_idempotency_and_external_reconcile(self):
        order, data = self.manual()
        self.assertEqual(order.total, 70000)
        self.assertIsNone(order.user_id)
        self.assertEqual(order.payment.status, 'UNPAID')
        self.assertEqual(order.pk, manual_order(self.staff, data, []).pk)
        with self.assertRaises(ValidationError):
            self.manual()
        with self.assertRaises(ValidationError):
            capture_cash(self.staff, order.public_code)
        reconcile_external(self.staff, order.public_code)
        reconcile_external(self.staff, order.public_code)
        self.assertEqual(order.payment.events.count(), 1)

    def test_manual_requires_staff_and_matching_option_product(self):
        from catalog.models import ProductOption
        data = {'channel': 'COUNTER', 'customer_name': 'DEMO', 'idempotency_key': uuid.uuid4()}
        with self.assertRaises(PermissionDenied):
            manual_order(self.buyer, data, [])
        option = ProductOption.objects.create(product=ProductVariant.objects.get(sku='CF01-STANDARD').product,
            name='Sai món', kind='TOPPING')
        with self.assertRaises(ValidationError):
            manual_order(self.staff, data, [{'variant': self.variant, 'quantity': 1, 'options': [option]}])

    def test_report_totals_cancel_exclusion_permissions_csv_and_dates(self):
        active = self.order()
        simulate_payment(self.buyer, active.payment.token, True)
        cancelled = self.order()
        transition_order(self.buyer, cancelled.public_code, 'CANCELLED')
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/dashboard/reports/').status_code, 403)
        self.client.force_login(self.admin)
        response = self.client.get('/dashboard/reports/')
        self.assertEqual(response.context['summary']['net'], 60000)
        self.assertEqual(response.context['summary']['collected'], 60000)
        self.assertEqual(response.context['cancelled'], 1)
        self.assertContains(self.client.get('/dashboard/reports/?format=csv'), 'WEB,1,60000,0,0,60000,60000')
        self.assertNotContains(self.client.get('/dashboard/reports/?format=csv'), '0900000000')
        self.assertEqual(self.client.get('/dashboard/reports/?channel=APP').context['summary']['orders'], 0)
        response = self.client.get('/dashboard/reports/?start=2026-10-20&end=2026-10-01')
        self.assertTrue(response.context['form'].errors)

    def test_operational_pages_and_customer_forbidden(self):
        for user, expected in [(self.buyer, 403), (self.staff, 200)]:
            self.client.force_login(user)
            for path in ['/dashboard/orders/new-manual/', '/dashboard/inventory/', '/dashboard/orders/']:
                self.assertEqual(self.client.get(path).status_code, expected)

    def test_http_shortage_rejection_has_audit_and_no_consumption(self):
        order = self.order()
        cup = Ingredient.objects.get(sku='DEMO-CUP')
        adjust_stock(self.admin, cup.pk, -balance(cup), 'Hết kho DEMO', uuid.uuid4())
        self.client.force_login(self.staff)
        from commerce.staff import version
        order.refresh_from_db()
        response=self.client.post(f'/dashboard/kitchen/{order.public_code}/action/', {'action': 'start', 'version': version(order)})
        self.assertEqual(response.status_code,400)
        self.assertIn('Không đủ nguyên liệu',response.json()['error'])
        order.refresh_from_db()
        self.assertEqual(order.status, 'CONFIRMED')
        self.assertFalse(order.history.filter(reason__contains='Từ chối thao tác').exists())
        self.assertFalse(StockMovement.objects.filter(order=order).exists())

    def test_topping_bom_consumption_and_missing_bom_block(self):
        from commerce.models import OptionRecipeLine
        topping = self.variant.product.options.get(name='Thạch DEMO')
        cart = Cart.objects.create(user=self.buyer)
        add_item(cart, self.variant.pk, 2, [topping.pk])
        order = place_order(self.buyer, cart, {'customer_name': 'DEMO', 'phone': '0900000000',
            'fulfillment': 'PICKUP', 'payment_method': 'MOCK_ONLINE', 'idempotency_key': uuid.uuid4()})
        jelly = Ingredient.objects.get(sku='DEMO-JELLY')
        before = balance(jelly)
        simulate_payment(self.buyer, order.payment.token, True)
        transition_order(self.staff, order.public_code, 'PREPARING')
        self.assertEqual(balance(jelly), before-40)
        OptionRecipeLine.objects.filter(option=topping).delete()
        add_item(cart, self.variant.pk, 1, [topping.pk])
        with self.assertRaises(ValidationError):
            place_order(self.buyer, cart, {'customer_name': 'DEMO', 'phone': '0900000000',
                'fulfillment': 'PICKUP', 'payment_method': 'MOCK_ONLINE', 'idempotency_key': uuid.uuid4()})
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(cart.items.get().quantity, 1)

    def test_manual_http_formset_uses_channel_price_and_prevents_repeat(self):
        self.client.force_login(self.staff)
        response = self.client.get('/dashboard/orders/new-manual/')
        key = response.context['form'].initial['idempotency_key']
        data = {'channel': 'COUNTER', 'customer_name': 'Khách DEMO', 'idempotency_key': key,
            'lines-TOTAL_FORMS': 1, 'lines-INITIAL_FORMS': 0, 'lines-MIN_NUM_FORMS': 1,
            'lines-MAX_NUM_FORMS': 10, 'lines-0-variant': self.variant.pk, 'lines-0-quantity': 3,
            'total': 1}
        self.assertEqual(self.client.post('/dashboard/orders/new-manual/', data).status_code, 302)
        self.assertEqual(self.client.post('/dashboard/orders/new-manual/', data).status_code, 302)
        self.assertEqual(Order.objects.filter(channel='COUNTER').count(), 1)
        self.assertEqual(Order.objects.get(channel='COUNTER').total, 90000)

    def test_web_service_rejects_external_payment_method(self):
        with self.assertRaises(ValidationError):
            self.order(payment_method='EXTERNAL_DEMO')
