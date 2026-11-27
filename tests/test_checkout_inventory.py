from commerce.services import simulate_payment
"""Check supply before accepting orders and preserve the agreed recipe."""
from decimal import Decimal
import uuid
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from catalog.models import ProductVariant
from commerce.models import Cart, Ingredient, Order, Payment, RecipeLine, OptionRecipeLine, StockMovement
from commerce.operations import adjust_stock, balance, manual_order
from commerce.services import add_item, place_order, transition_order


class CheckoutInventoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.user = User.objects.create_user('inventory-check-buyer')
        cls.user.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.admin = User.objects.create_user('inventory-check-admin')
        cls.admin.groups.add(Group.objects.get(name='ADMIN'))
        cls.variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        cls.cup = Ingredient.objects.get(sku='DEMO-CUP')

    def setUp(self):
        self.cart = Cart.objects.create(user=self.user)

    def data(self, **updates):
        return {'customer_name': 'DEMO', 'phone': '0900000000', 'fulfillment': 'PICKUP',
            'payment_method': 'MOCK_ONLINE', 'idempotency_key': uuid.uuid4(), **updates}

    def test_shortage_rejects_order_payment_and_preserves_cart(self):
        adjust_stock(self.admin, self.cup.pk, Decimal(1)-balance(self.cup), 'Chỉ còn một ly DEMO', uuid.uuid4())
        add_item(self.cart, self.variant.pk, 2)
        with self.assertRaisesMessage(ValidationError, 'Không đủ nguyên liệu'):
            place_order(self.user, self.cart, self.data())
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Payment.objects.exists())
        self.assertEqual(self.cart.items.get().quantity, 2)

    def test_combined_lines_cannot_each_reuse_the_last_cup(self):
        adjust_stock(self.admin, self.cup.pk, Decimal(1)-balance(self.cup), 'Một ly cho cả giỏ', uuid.uuid4())
        add_item(self.cart, self.variant.pk, 1)
        add_item(self.cart, ProductVariant.objects.get(sku='CF01-STANDARD').pk, 1)
        with self.assertRaises(ValidationError):
            place_order(self.user, self.cart, self.data())
        self.assertEqual(self.cart.items.count(), 2)
        self.assertFalse(Order.objects.exists())

    def test_checkout_saves_exact_recipe_without_deducting_stock_or_trusting_client(self):
        add_item(self.cart, self.variant.pk, 2)
        before = balance(self.cup)
        order = place_order(self.user, self.cart, self.data(recipe_snapshot=[{'ingredient_id': 1, 'quantity': '0'}]))
        item = order.items.get()
        cup = next(row for row in item.recipe_snapshot if row['ingredient_id'] == self.cup.pk)
        self.assertEqual(Decimal(cup['quantity']), 1)
        self.assertEqual(cup['unit'], 'piece')
        self.assertEqual(balance(self.cup), before)
        self.assertFalse(StockMovement.objects.filter(order=order).exists())

    def test_recipe_edits_after_checkout_do_not_change_consumption(self):
        add_item(self.cart, self.variant.pk, 2)
        order = place_order(self.user, self.cart, self.data())
        RecipeLine.objects.filter(variant=self.variant, ingredient=self.cup).update(quantity=5)
        before = balance(self.cup)
        simulate_payment(self.user, order.payment.token, True)
        transition_order(self.admin, order.public_code, 'PREPARING')
        simulate_payment(self.user, order.payment.token, True)
        transition_order(self.admin, order.public_code, 'PREPARING')
        self.assertEqual(balance(self.cup), before-2)
        self.assertEqual(StockMovement.objects.filter(order=order, ingredient=self.cup).count(), 1)

    def test_topping_recipe_is_saved_and_survives_later_removal(self):
        topping = self.variant.product.options.get(name='Thạch DEMO')
        jelly = Ingredient.objects.get(sku='DEMO-JELLY')
        add_item(self.cart, self.variant.pk, 2, [topping.pk])
        order = place_order(self.user, self.cart, self.data())
        OptionRecipeLine.objects.filter(option=topping).delete()
        before = balance(jelly)
        simulate_payment(self.user, order.payment.token, True)
        transition_order(self.admin, order.public_code, 'PREPARING')
        self.assertEqual(balance(jelly), before-40)

    def test_missing_base_recipe_and_inactive_ingredient_rejected_at_checkout(self):
        add_item(self.cart, self.variant.pk, 1)
        Ingredient.objects.filter(pk=self.cup.pk).update(is_active=False)
        with self.assertRaises(ValidationError):
            place_order(self.user, self.cart, self.data())
        Ingredient.objects.filter(pk=self.cup.pk).update(is_active=True)
        RecipeLine.objects.filter(variant=self.variant).delete()
        with self.assertRaisesMessage(ValidationError, 'Chưa có công thức'):
            place_order(self.user, self.cart, self.data())
        self.assertFalse(Order.objects.exists())

    def test_stock_and_unit_changes_after_checkout_still_block_preparation(self):
        add_item(self.cart, self.variant.pk, 1)
        order = place_order(self.user, self.cart, self.data())
        Ingredient.objects.filter(pk=self.cup.pk).update(unit='g')
        with self.assertRaisesMessage(ValidationError, 'Đơn vị nguyên liệu'):
            simulate_payment(self.user, order.payment.token, True)
            transition_order(self.admin, order.public_code, 'PREPARING')
        order.refresh_from_db()
        self.assertEqual(order.status, 'CONFIRMED')
        self.assertFalse(StockMovement.objects.filter(order=order).exists())

    def test_legacy_order_captures_recipe_at_preparation_with_honest_audit(self):
        add_item(self.cart, self.variant.pk, 1)
        order = place_order(self.user, self.cart, self.data())
        order.items.update(recipe_snapshot=None)
        simulate_payment(self.user, order.payment.token, True)
        transition_order(self.admin, order.public_code, 'PREPARING')
        self.assertTrue(order.items.get().recipe_snapshot)
        self.assertTrue(order.history.filter(reason__contains='Đơn cũ: chốt công thức hiện tại').exists())

    def test_corrupt_snapshot_fails_closed_without_ledger_writes(self):
        add_item(self.cart, self.variant.pk, 1)
        order = place_order(self.user, self.cart, self.data())
        order.items.update(recipe_snapshot=[{'ingredient_id': self.cup.pk, 'unit': 'piece', 'quantity': 'NaN'}])
        with self.assertRaises(ValidationError):
            simulate_payment(self.user, order.payment.token, True)
            transition_order(self.admin, order.public_code, 'PREPARING')
        self.assertFalse(StockMovement.objects.filter(order=order).exists())

    def test_manual_orders_also_validate_supply_and_capture_recipe(self):
        data = {'channel': 'COUNTER', 'customer_name': 'DEMO', 'idempotency_key': uuid.uuid4()}
        before = balance(self.cup)
        first = manual_order(self.admin, data, [{'variant': self.variant, 'quantity': 2}])
        self.assertTrue(first.items.get().recipe_snapshot)
        self.assertEqual(balance(self.cup), before)
        adjust_stock(self.admin, self.cup.pk, Decimal(1)-balance(self.cup), 'Một ly DEMO còn lại', uuid.uuid4())
        with self.assertRaises(ValidationError):
            manual_order(self.admin, dict(data, idempotency_key=uuid.uuid4()), [{'variant': self.variant, 'quantity': 2}])
        self.assertEqual(Order.objects.count(), 1)
