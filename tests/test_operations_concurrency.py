from commerce.services import simulate_payment
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal
import uuid
from unittest import skipUnless
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connections, connection, transaction
from django.test import TransactionTestCase
from catalog.models import ProductVariant
from commerce.models import Cart, Ingredient, Order, StoreSettings, StockMovement
from commerce.operations import balance, adjust_stock, scheduled_slot
from commerce.services import add_item, place_order, transition_order


@skipUnless(connection.vendor == 'postgresql', 'Requires real PostgreSQL row locks')
class OperationsConcurrencyTests(TransactionTestCase):
    def setUp(self):
        call_command('seed_demo', verbosity=0)
        self.staff = User.objects.create_user('race-stock-staff')
        self.staff.groups.add(Group.objects.get(name='STAFF'))
        self.admin = User.objects.create_user('race-stock-admin')
        self.admin.groups.add(Group.objects.get(name='ADMIN'))
        self.users, self.carts = [], []
        variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        for index in range(2):
            user = User.objects.create_user(f'ops-race-{index}')
            user.groups.add(Group.objects.get(name='CUSTOMER'))
            cart = Cart.objects.create(user=user)
            add_item(cart, variant.pk, 1)
            self.users.append(user)
            self.carts.append(cart)

    def data(self, **updates):
        return {'customer_name': 'DEMO', 'phone': '0900000000', 'fulfillment': 'PICKUP',
            'payment_method': 'MOCK_ONLINE', 'idempotency_key': uuid.uuid4(), **updates}

    def race(self, action):
        barrier = Barrier(2)
        def worker(index):
            try:
                connections['default'].ensure_connection()
                barrier.wait(timeout=10)
                try:
                    action(index)
                    return 'ok'
                except ValidationError:
                    return 'rejected'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, range(2)))

    def test_last_cup_cannot_be_consumed_twice(self):
        orders = [place_order(self.users[i], self.carts[i], self.data()) for i in range(2)]
        for i, order in enumerate(orders):
            simulate_payment(self.users[i], order.payment.token, True)
        cup = Ingredient.objects.get(sku='DEMO-CUP')
        adjust_stock(self.admin, cup.pk, Decimal(1)-balance(cup), 'Chỉ còn 1 ly DEMO', uuid.uuid4())
        results = self.race(lambda index: transition_order(self.staff, orders[index].public_code, 'PREPARING'))
        self.assertCountEqual(results, ['ok', 'rejected'])
        self.assertEqual(balance(cup), 0)
        self.assertEqual(Order.objects.filter(status='PREPARING').count(), 1)
        self.assertEqual(StockMovement.objects.filter(ingredient=cup, reason='CONSUME').count(), 1)

    def test_last_slot_cannot_be_booked_twice(self):
        with transaction.atomic():
            slot = scheduled_slot()
        from datetime import timedelta
        # Restrict opening hours/horizon so only this one slot remains.
        StoreSettings.objects.filter(name='DEMO').update(slot_capacity=1, preorder_days=1,
            opens_at=slot.time(), closes_at=(slot+timedelta(minutes=15)).time())
        Order.objects.create(user=self.users[0],customer_name='Full tomorrow fixture',phone='0900000000',
            fulfillment='PICKUP',status='CONFIRMED',subtotal=0,total=0,idempotency_key=uuid.uuid4(),
            scheduled_for=slot+timedelta(days=1))
        results = self.race(lambda index: place_order(self.users[index], self.carts[index],
            self.data(scheduled_for=slot,menu_started_at=slot-timedelta(minutes=35))))
        self.assertCountEqual(results, ['ok', 'rejected'])
        self.assertEqual(Order.objects.filter(scheduled_for=slot).count(), 1)
