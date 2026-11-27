"""Django integration regression. Execute ONLY via guarded PostgreSQL TEST runner."""
import uuid
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from catalog.models import ProductVariant
from commerce.models import Cart, Order, Payment
from commerce.services import add_item, quote_cart, place_order, transition_order, verify_demo_transfer, capture_cash


@override_settings(NAU_DEMO_DELIVERY_ENABLED=True, NAU_STANDARD_MENU_ENABLED=False)
class DemoDeliveryCheckoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.buyer = User.objects.create_user('delivery-demo-buyer')
        cls.buyer.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.staff = User.objects.create_user('delivery-demo-staff')
        cls.staff.groups.add(Group.objects.get(name='STAFF'))
        cls.variant = ProductVariant.objects.get(sku='CF02-STANDARD')

    def setUp(self):
        self.cart = Cart.objects.create(user=self.buyer)
        add_item(self.cart, self.variant.pk, 4)

    def details(self, address='Địa chỉ demo A', method='COD'):
        return {
            'customer_name': 'Khách demo', 'phone': '0900000000',
            'fulfillment': 'DELIVERY', 'address': address, 'payment_method': method,
            'idempotency_key': uuid.uuid4(), 'voucher_code': '',
        }

    def create(self, **data):
        values = self.details(**data)
        # Historical delivery fixture, created only by the guarded TEST runner.
        # New WEB checkout must reject delivery even with the old env flag enabled.
        from commerce.demo_delivery import quote_demo_delivery
        q = quote_demo_delivery(values['address'], 120000, 0)
        order = Order.objects.create(user=self.buyer, customer_name=values['customer_name'],
            phone=values['phone'], fulfillment='DELIVERY', address=values['address'],
            subtotal=120000, shipping=q.shipping_vnd, total=120000+q.shipping_vnd,
            delivery_distance_km=Decimal(q.distance_meters)/1000,
            status='PENDING_CONFIRMATION', idempotency_key=values['idempotency_key'])
        Payment.objects.create(order=order, method=values['payment_method'], amount=order.total, status='UNPAID')
        return order

    def test_quote_rejects_outside_and_calculates_inside(self):
        for address in ('Địa chỉ demo A', 'Địa chỉ demo B', 'Địa chỉ không có trong demo'):
            with self.subTest(address=address), self.assertRaises(ValidationError):
                quote_cart(self.cart, self.buyer, 'DELIVERY')
            with self.subTest(address=address), self.assertRaises(ValidationError):
                place_order(self.buyer, self.cart, self.details(address=address))
        self.assertFalse(Order.objects.exists())

    def test_cod_waits_for_staff_then_issues_bill(self):
        order = self.create()
        self.assertEqual(order.status, 'PENDING_CONFIRMATION')
        self.assertFalse(order.delivery_verified)
        self.assertIsNone(order.bill_issued_at)
        transition_order(self.staff, order.public_code, 'CONFIRMED')
        order.refresh_from_db()
        self.assertTrue(order.delivery_verified)
        self.assertEqual(order.status, 'CONFIRMED')
        self.assertEqual(order.delivery_deadline_at - order.bill_issued_at, timedelta(minutes=60))
        self.assertEqual(order.payment.status, 'UNPAID')
        with self.assertRaises(ValidationError):
            capture_cash(self.staff, order.public_code)

    def test_bank_transfer_does_not_auto_mark_paid(self):
        order = self.create(method='BANK_TRANSFER_DEMO')
        transition_order(self.staff, order.public_code, 'CONFIRMED')
        with self.assertRaises(ValidationError):
            transition_order(self.staff, order.public_code, 'PREPARING')
        verify_demo_transfer(self.staff, order.public_code)
        order.refresh_from_db()
        self.assertEqual(order.payment.status, 'PAID')

    def test_outside_address_fails_without_order(self):
        with self.assertRaises(ValidationError):
            place_order(self.buyer, self.cart, self.details(address='Địa chỉ demo B'))
        self.assertFalse(Order.objects.exists())
        self.assertTrue(self.cart.items.exists())

    def test_late_delivery_detection(self):
        order = self.create()
        transition_order(self.staff, order.public_code, 'CONFIRMED')
        Order.objects.filter(pk=order.pk).update(
            status='DELIVERING',
            bill_issued_at=timezone.now() - timedelta(minutes=62),
            delivery_deadline_at=timezone.now() - timedelta(minutes=2),
        )
        order.refresh_from_db()
        self.assertTrue(order.delivery_is_late)
