import uuid
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from catalog.models import ProductVariant, ProductOption
from commerce.models import (Cart, CartItem, Order, OrderItem, Payment, PaymentEvent,
    OrderStatusHistory, Voucher, VoucherRedemption, StoreSettings)
from commerce.services import add_item


class CommerceSchemaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.user = User.objects.create_user('schema-customer')
        cls.variant = ProductVariant.objects.get(sku='CF01-STANDARD')

    def order(self, **updates):
        values = dict(user=self.user, channel='WEB', fulfillment='PICKUP', customer_name='DEMO', phone='000',
            subtotal=25000, total=25000, status='CONFIRMED', idempotency_key=uuid.uuid4())
        values.update(updates)
        return Order.objects.create(**values)

    def invalid(self, callback):
        with self.assertRaises(IntegrityError), transaction.atomic():
            callback()

    def test_all_commerce_tables_and_m2m_created(self):
        tables = connection.introspection.table_names()
        for model in [Cart, CartItem, Order, OrderItem, Payment, PaymentEvent,
                      OrderStatusHistory, Voucher, VoucherRedemption, StoreSettings]:
            self.assertIn(model._meta.db_table, tables)
        self.assertIn(CartItem.options.through._meta.db_table, tables)

    def test_named_constraints_are_present_in_real_database(self):
        with connection.cursor() as cursor:
            for model in [Cart, CartItem, Order, OrderItem, PaymentEvent, Voucher]:
                actual = connection.introspection.get_constraints(cursor, model._meta.db_table)
                for constraint in model._meta.constraints:
                    self.assertIn(constraint.name, actual)

    def test_staff_cannot_post_user_role_changes(self):
        from django.contrib.auth.models import Group
        user = User.objects.create_user('ops-staff', is_staff=True)
        user.groups.add(Group.objects.get(name='STAFF'))
        self.client.force_login(user)
        response = self.client.post(f'/admin/auth/user/{self.user.pk}/change/', {'is_superuser':'on'})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_superuser)

    def test_cart_owner_requires_exactly_one_user_or_session(self):
        self.invalid(lambda: Cart.objects.create())
        self.invalid(lambda: Cart.objects.create(user=self.user, session_key=uuid.uuid4()))
        Cart.objects.create(user=self.user)
        self.invalid(lambda: Cart.objects.create(user=self.user))

    def test_cart_qty_constraint_and_configuration_unique(self):
        cart = Cart.objects.create(user=self.user)
        for qty in [0, 100]:
            self.invalid(lambda: CartItem.objects.create(cart=cart, variant=self.variant, quantity=qty, config_key='same'))
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2, config_key='same')
        self.invalid(lambda: CartItem.objects.create(cart=cart, variant=self.variant, quantity=1, config_key='same'))

    def test_guest_cart_survives_login_and_merges_once(self):
        session = self.client.session
        key = uuid.uuid4()
        session['guest_cart_key'] = str(key)
        session.save()
        guest = Cart.objects.create(session_key=key)
        add_item(guest, self.variant.pk, 2)
        own = Cart.objects.create(user=self.user)
        add_item(own, self.variant.pk, 1)
        self.client.force_login(self.user)
        self.assertEqual(own.items.get().quantity, 3)
        self.client.force_login(self.user)
        self.assertEqual(own.items.get().quantity, 3)
        self.assertFalse(Cart.objects.filter(pk=guest.pk).exists())

    def test_option_relation_and_configuration_validation(self):
        from django.core.exceptions import ValidationError
        cart = Cart.objects.create(user=self.user)
        option = ProductOption.objects.create(product=self.variant.product, kind='TOPPING', name='Demo', price_delta=8000)
        line = add_item(cart, self.variant.pk, 2, [option.pk])
        self.assertEqual(list(line.options.all()), [option])
        other = ProductOption.objects.create(product=ProductVariant.objects.get(sku='CF02-STANDARD').product,
            kind='ICE', name='Không đá')
        with self.assertRaises(ValidationError):
            add_item(cart, self.variant.pk, 1, [other.pk])

    def test_order_total_discount_and_user_constraints(self):
        self.invalid(lambda: self.order(total=1))
        self.invalid(lambda: self.order(discount=26000, total=0))
        self.invalid(lambda: self.order(user=None))
        order = self.order(discount=5000, shipping=15000, total=35000)
        self.assertEqual(order.total, 35000)

    def test_order_idempotency_and_snapshot_preservation(self):
        order = self.order()
        self.invalid(lambda: self.order(idempotency_key=order.idempotency_key))
        item = OrderItem.objects.create(order=order, variant=self.variant, product_name='Tên lúc mua',
            sku=self.variant.sku, unit_price=25000, quantity=2, line_total=50000)
        self.variant.product.name = 'Tên sau sửa'
        self.variant.product.save()
        item.refresh_from_db()
        self.assertEqual(item.product_name, 'Tên lúc mua')
        with self.assertRaises(ProtectedError):
            self.variant.delete()

    def test_order_item_quantity_and_line_total(self):
        order = self.order()
        for qty, total in [(0, 0), (100, 2500000), (2, 1)]:
            self.invalid(lambda: OrderItem.objects.create(order=order, variant=self.variant,
                product_name='demo', sku='demo', unit_price=25000, quantity=qty, line_total=total))

    def test_payment_one_per_order_event_idempotency_and_history_actor(self):
        order = self.order()
        payment = Payment.objects.create(order=order, method='PAY_AT_PICKUP', status='UNPAID', amount=25000)
        self.invalid(lambda: Payment.objects.create(order=order, method='COD', status='UNPAID', amount=25000))
        PaymentEvent.objects.create(payment=payment, event_key='success', actor=self.user)
        self.invalid(lambda: PaymentEvent.objects.create(payment=payment, event_key='success', actor=self.user))
        history = OrderStatusHistory.objects.create(order=order, from_state='', to_state='CONFIRMED', actor=self.user)
        order.refresh_from_db()
        self.assertEqual(order.payment, payment)
        self.assertEqual(order.history.get().actor, history.actor)

    def voucher(self, **updates):
        values = dict(code='NAU10', kind='PERCENT', amount=10, starts_at=timezone.now(),
            ends_at=timezone.now()+timedelta(days=1))
        values.update(updates)
        return Voucher.objects.create(**values)

    def test_voucher_case_uniqueness_and_bounds(self):
        voucher = self.voucher()
        self.invalid(lambda: self.voucher(code='nau10'))
        for data in [{'code':'bad1', 'amount':101}, {'code':'bad2', 'amount':0},
                     {'code':'bad3', 'max_uses':0}, {'code':'bad4', 'ends_at':timezone.now()-timedelta(days=1)}]:
            self.invalid(lambda: self.voucher(**data))
        self.assertEqual(voucher.code, 'NAU10')

    def test_redemption_one_per_order_and_protected_voucher(self):
        order, voucher = self.order(), self.voucher()
        VoucherRedemption.objects.create(order=order, voucher=voucher, user=self.user)
        self.invalid(lambda: VoucherRedemption.objects.create(order=order, voucher=voucher, user=self.user))
        with self.assertRaises(ProtectedError):
            voucher.delete()
