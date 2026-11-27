from commerce.services import simulate_payment
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest import skipUnless
from threading import Barrier
import uuid
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, connections
from django.test import TransactionTestCase
from django.utils import timezone
from catalog.models import ProductVariant
from commerce.models import Cart, Order, Voucher, VoucherRedemption
from commerce.services import add_item, place_order


@skipUnless(connection.vendor == 'postgresql', 'Requires real PostgreSQL row locks')
class CommerceConcurrencyTests(TransactionTestCase):
    def setUp(self):
        call_command('seed_demo', verbosity=0)
        self.users, self.carts = [], []
        self.barrier = Barrier(2)
        variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        for index in range(2):
            user = User.objects.create_user(f'concurrent-{index}')
            user.groups.add(Group.objects.get(name='CUSTOMER'))
            cart = Cart.objects.create(user=user)
            add_item(cart, variant.pk, 4)
            self.users.append(user)
            self.carts.append(cart)

    def submit(self, index, key, voucher=''):
        try:
            connections['default'].ensure_connection()
            self.barrier.wait(timeout=10)
            data = {'customer_name':'DEMO', 'phone':'0900000000', 'fulfillment':'PICKUP',
                'payment_method':'MOCK_ONLINE', 'idempotency_key':key, 'voucher_code':voucher}
            try:
                return ('created', place_order(self.users[index], self.carts[index], data).pk)
            except ValidationError:
                return ('rejected', None)
        finally:
            connections.close_all()

    def test_simultaneous_double_submit_creates_exactly_one_order(self):
        key = uuid.uuid4()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.submit(0, key), range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(Order.objects.count(), 1)

    def test_simultaneous_voucher_last_use_cannot_be_overspent(self):
        Voucher.objects.create(code='LAST', kind='PERCENT', amount=10, max_uses=1,
            starts_at=timezone.now()-timedelta(days=1), ends_at=timezone.now()+timedelta(days=1))
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda index: self.submit(index, uuid.uuid4(), 'LAST'), range(2)))
        self.assertCountEqual([result[0] for result in results], ['created', 'rejected'])
        self.assertEqual(VoucherRedemption.objects.filter(is_active=True).count(), 1)
        self.assertEqual(Order.objects.count(), 1)
