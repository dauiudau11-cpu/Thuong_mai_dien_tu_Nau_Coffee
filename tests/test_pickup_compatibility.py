"""Replay real anonymized catalog/BOM/history exclusively in nau_coffee_test."""
from collections import defaultdict
from decimal import Decimal
import uuid
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.test import TestCase, override_settings
from catalog.approved_menu import MENU
from catalog.models import ProductVariant, ChannelPrice, StandardCost
from commerce.models import Cart, Ingredient, Order, Payment, RecipeLine, StockMovement
from commerce.operations import balance
from commerce.services import add_item, place_order, simulate_payment, transition_order, refund_mock
from .pickup_compatibility_fixture import load_compatibility_fixture, create_role_user, history_state


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class CopiedDevelopmentCompatibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.payload=load_compatibility_fixture()
        cls.buyer=create_role_user('compatibility-buyer','CUSTOMER')
        cls.staff=create_role_user('compatibility-staff','STAFF')
        cls.admin=create_role_user('compatibility-admin','ADMIN')

    def setUp(self):
        self.before=history_state()
        self.cart=Cart.objects.create(user=self.buyer)

    def tearDown(self):
        self.assertEqual(history_state(),self.before,'Copied historical rows must remain byte-for-value unchanged')

    def create_order(self,sku='CF02-360',quantity=2):
        add_item(self.cart,ProductVariant.objects.get(sku=sku).pk,quantity)
        return place_order(self.buyer,self.cart,dict(customer_name='Compatibility buyer',phone='0900000000',
            fulfillment='PICKUP',payment_method='MOCK_ONLINE',idempotency_key=uuid.uuid4()))

    def test_exact_eight_prices_costs_fifteen_ingredients_fifty_bom(self):
        self.assertEqual(ProductVariant.objects.count(),21)
        self.assertEqual(Ingredient.objects.count(),15)
        self.assertEqual(RecipeLine.objects.count(),50)
        for code,name,ml,cost,web,app in MENU:
            variant=ProductVariant.objects.get(sku=f'{code}-{ml}')
            self.assertEqual((variant.product.name,variant.volume_ml,variant.is_available),(name,ml,True))
            self.assertEqual(dict(variant.prices.values_list('channel','original_price')),dict(WEB=web,COUNTER=web,APP=app))
            self.assertEqual(StandardCost.objects.get(variant=variant).ingredient_cost,cost)
            order=self.create_order(variant.sku,1)
            self.assertEqual(order.total,web)
            self.assertEqual(order.shipping,0)
            self.assertEqual(order.items.get().recipe_snapshot,
                [dict(ingredient_id=line.ingredient_id,name=line.ingredient.name,unit=line.ingredient.unit,quantity=str(line.quantity))
                 for line in variant.recipe.select_related('ingredient').order_by('ingredient_id')])
        self.assertEqual(Order.objects.count(),13)

    def test_full_pickup_pipeline_consumes_exact_copied_recipe_once(self):
        order=self.create_order()
        before={i.pk:balance(i) for i in Ingredient.objects.all()}
        self.assertEqual(order.total,64000)
        simulate_payment(self.buyer,order.payment.token,False)
        order.refresh_from_db();self.assertEqual(order.status,'PENDING_PAYMENT')
        for _ in range(2):simulate_payment(self.buyer,order.payment.token,True)
        self.assertEqual(before,{i.pk:balance(i) for i in Ingredient.objects.all()})
        for _ in range(2):transition_order(self.staff,order.public_code,'PREPARING')
        needs={line.ingredient_id:line.quantity*2 for line in RecipeLine.objects.filter(variant__sku='CF02-360')}
        self.assertEqual({i.pk:balance(i) for i in Ingredient.objects.all()},
            {pk:amount-needs.get(pk,0) for pk,amount in before.items()})
        self.assertEqual(StockMovement.objects.filter(order=order).count(),6)
        with self.assertRaises(ValidationError):transition_order(self.buyer,order.public_code,'CANCELLED')
        for state in ['READY','PICKUP_WAITING','COMPLETED']:transition_order(self.staff,order.public_code,state)
        order.refresh_from_db();self.assertEqual(order.status,'COMPLETED')
        self.assertEqual(order.history.filter(to_state='CONFIRMED').count(),1)
        self.assertEqual(order.payment.events.filter(event_key='mock_success').count(),1)

    def test_paid_and_unpaid_cancellation_refund_on_copied_data(self):
        before=StockMovement.objects.count()
        unpaid=self.create_order('CF01-360',1)
        transition_order(self.buyer,unpaid.public_code,'CANCELLED')
        simulate_payment(self.buyer,unpaid.payment.token,True)
        unpaid.refresh_from_db();self.assertEqual(unpaid.payment.status,'PENDING')
        paid=self.create_order('CF03-360',1)
        simulate_payment(self.buyer,paid.payment.token,True)
        for _ in range(2):transition_order(self.buyer,paid.public_code,'CANCELLED')
        paid.refresh_from_db();self.assertEqual(paid.payment.status,'REFUND_PENDING')
        for _ in range(2):refund_mock(self.admin,paid.public_code)
        simulate_payment(self.buyer,paid.payment.token,True)
        paid.refresh_from_db();self.assertEqual(paid.payment.status,'REFUNDED')
        self.assertEqual(paid.payment.events.filter(event_key='mock_refund').count(),1)
        self.assertEqual(StockMovement.objects.count(),before)

    def test_every_existing_order_remains_readable_without_mutating_rows(self):
        for order in Order.objects.all():
            self.client.force_login(order.user)
            response=self.client.get(f'/account/orders/{order.public_code}/')
            self.assertEqual(response.status_code,200)
            self.assertContains(response,order.items.get().sku)
        self.client.force_login(self.staff)
        for path in ['/dashboard/','/dashboard/orders/','/dashboard/kitchen/','/dashboard/inventory/']:
            self.assertEqual(self.client.get(path).status_code,200)
        self.client.force_login(self.admin)
        self.assertContains(self.client.get('/dashboard/settings/payment/'),'Chỉ thanh toán trực tuyến mô phỏng')
        response=self.client.get('/dashboard/settings/delivery/')
        self.assertContains(response,'Chỉ đặt trước và nhận tại quán')
        self.assertContains(response,'không áp dụng WEB mới')

    def test_legacy_unmapped_recipe_blocks_preparation_without_rewriting_history(self):
        legacy=Order.objects.get(pk=1)
        self.assertEqual(legacy.status,'CONFIRMED')
        self.assertIsNone(legacy.items.get().recipe_snapshot)
        self.assertFalse(legacy.items.get().variant.recipe.exists())
        with self.assertRaisesMessage(ValidationError,'Đơn cũ thiếu công thức'):
            transition_order(self.staff,legacy.public_code,'PREPARING')
        self.assertEqual(history_state(),self.before)
