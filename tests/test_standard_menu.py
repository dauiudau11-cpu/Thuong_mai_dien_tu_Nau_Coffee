from commerce.services import simulate_payment
"""Rollout rehearsal only: fixtures and all writes stay in the guarded test DB."""
import io
import uuid
from unittest.mock import patch
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings, RequestFactory
from django.contrib import admin
from catalog.approved_menu import MENU
from catalog.models import Product, ProductVariant, ChannelPrice, StandardCost
from catalog.admin import PriceForm
from commerce.models import Cart, CartItem, Order, OrderItem, Payment, RecipeLine, Ingredient, StockMovement
from commerce.services import add_item, quote_cart, place_order
from commerce.operations import manual_order


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class StandardMenuTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=io.StringIO())
        cls.buyer = User.objects.create_user('standard-buyer')
        cls.buyer.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.staff = User.objects.create_user('standard-staff', is_staff=True)
        cls.staff.groups.add(Group.objects.get(name='STAFF'))
        cls.admin = User.objects.create_user('standard-admin', is_staff=True)
        cls.admin.groups.add(Group.objects.get(name='ADMIN'))
        # Only test data: include a legacy delivery order to prove no rewrite.
        cls.old = Order.objects.create(user=cls.buyer, customer_name='Fixture', phone='00000000',
            fulfillment='DELIVERY', address='Fixture address', subtotal=75000, total=75000,
            status='CONFIRMED', idempotency_key=uuid.uuid4())
        OrderItem.objects.create(order=cls.old, variant=ProductVariant.objects.get(sku='CF01-STANDARD'),
            product_name='Cà phê đen đá', sku='CF01-STANDARD', unit_price=25000, quantity=3,
            line_total=75000, recipe_snapshot=None)
        Payment.objects.create(order=cls.old, method='COD', status='UNPAID', amount=75000)

    def setUp(self):
        self.cart = Cart.objects.create(user=self.buyer)

    def rollout(self, **kwargs):
        call_command('prepare_standard_menu', apply=True, cutover=True, stdout=io.StringIO(), **kwargs)

    def data(self, **kwargs):
        return dict(customer_name='Fixture', phone='0900000000', fulfillment='PICKUP',
            payment_method='MOCK_ONLINE', idempotency_key=uuid.uuid4(), **kwargs)

    def supply(self):
        # Explicit test-only ingredient and stock; never written by rollout command.
        ingredient = Ingredient.objects.create(sku='TEST-STANDARD-CUP', name='Test only cup', unit='piece')
        StockMovement.objects.create(ingredient=ingredient, delta=1000, reason='PURCHASE',
            actor=self.admin, idempotency_key=uuid.uuid4())
        for variant in ProductVariant.objects.filter(size='FIXED'):
            RecipeLine.objects.create(variant=variant, ingredient=ingredient, quantity=1)

    def test_preview_is_read_only(self):
        before = [list(model.objects.order_by('pk').values()) for model in (Product, ProductVariant, ChannelPrice, StandardCost)]
        call_command('prepare_standard_menu', stdout=io.StringIO())
        self.assertEqual(before, [list(model.objects.order_by('pk').values()) for model in (Product, ProductVariant, ChannelPrice, StandardCost)])

    def test_exact_prices_sizes_costs_and_rerun_without_changes(self):
        old = list(ProductVariant.objects.order_by('pk').values('id','sku','size','volume_ml'))
        prices = list(ChannelPrice.objects.order_by('pk').values())
        orders = [list(m.objects.order_by('pk').values()) for m in (Order,OrderItem,Payment)]
        self.rollout()
        self.assertEqual(ProductVariant.objects.count(), 21)
        self.assertEqual(ChannelPrice.objects.count(), 63)
        self.assertEqual(StandardCost.objects.count(), 8)
        self.assertFalse(ProductVariant.objects.filter(is_available=True).exists())
        self.assertEqual(old, list(ProductVariant.objects.exclude(size='FIXED').order_by('pk').values('id','sku','size','volume_ml')))
        self.assertEqual(prices, list(ChannelPrice.objects.filter(variant__size__in=['STANDARD','M','L']).order_by('pk').values()))
        for code,name,ml,cost,web,app in MENU:
            v = ProductVariant.objects.get(sku=f'{code}-{ml}')
            self.assertEqual((v.product.name,v.size,v.volume_ml,v.standard_cost.ingredient_cost),(name,'FIXED',ml,cost))
            self.assertEqual(dict(v.prices.values_list('channel','original_price')),{'WEB':web,'COUNTER':web,'APP':app})
        self.assertEqual(orders,[list(m.objects.order_by('pk').values()) for m in (Order,OrderItem,Payment)])
        before = [list(m.objects.order_by('pk').values()) for m in (Product,ProductVariant,ChannelPrice,StandardCost)]
        self.rollout()
        self.assertEqual(before,[list(m.objects.order_by('pk').values()) for m in (Product,ProductVariant,ChannelPrice,StandardCost)])

    def test_conflicting_target_price_rolls_back_all_updates(self):
        self.rollout()
        ChannelPrice.objects.filter(variant__sku='OT02-700',channel='APP').update(original_price=1)
        Product.objects.filter(code='CF01').update(name='Cà phê đen đá')
        before = list(Product.objects.order_by('pk').values())
        with self.assertRaises(CommandError): self.rollout()
        self.assertEqual(before,list(Product.objects.order_by('pk').values()))

    def test_injected_write_error_rolls_back_creation_and_names(self):
        names = list(Product.objects.order_by('pk').values_list('name',flat=True))
        with patch('catalog.management.commands.prepare_standard_menu.StandardCost.objects.create',side_effect=RuntimeError('test fault')):
            with self.assertRaises(CommandError): self.rollout()
        self.assertEqual(ProductVariant.objects.count(),13)
        self.assertEqual(ChannelPrice.objects.count(),39)
        self.assertEqual(names,list(Product.objects.order_by('pk').values_list('name',flat=True)))

    def test_dev_target_is_refused_before_queries_or_writes(self):
        from django.db import connection
        with patch.dict(connection.settings_dict,NAME='nau_coffee_dev',USER='nau_coffee_app'):
            with self.assertRaises(CommandError): self.rollout()
        self.assertEqual(ProductVariant.objects.count(),13)

    def test_activation_without_bom_fails_and_preserves_paused_catalog(self):
        self.rollout()
        before = list(ProductVariant.objects.order_by('pk').values())
        with self.assertRaises(CommandError): self.rollout(activate=True)
        self.assertEqual(before,list(ProductVariant.objects.order_by('pk').values()))
        self.assertEqual(RecipeLine.objects.filter(variant__size='FIXED').count(),0)

    def test_legacy_cf04_cart_preserved_and_customer_told_to_choose_again(self):
        v=ProductVariant.objects.get(sku='CF04-M')
        row=CartItem.objects.create(cart=self.cart,variant=v,quantity=2,config_key='fixture')
        before=list(self.cart.items.values())
        self.rollout()
        with self.assertRaisesMessage(ValidationError,'vui lòng chọn lại'):quote_cart(self.cart,self.buyer)
        self.client.force_login(self.buyer)
        self.assertContains(self.client.get('/cart/'),'Lựa chọn cũ đã ngừng bán')
        self.assertEqual(before,list(self.cart.items.values()))
        row.refresh_from_db()
        self.assertEqual((row.variant_id,row.variant.volume_ml,row.quantity),(v.pk,350,2))

    def test_paused_products_visible_with_prices_but_cannot_add_or_checkout(self):
        self.rollout()
        self.assertEqual(len(self.client.get('/menu/').context['page_obj']),8)
        for code,name,ml,cost,web,app in MENU:
            v=ProductVariant.objects.get(sku=f'{code}-{ml}')
            response=self.client.get('/products/'+v.product.slug+'/')
            self.assertContains(response,'Tạm chưa nhận đặt món')
            self.assertNotContains(response,'<button>Thêm vào giỏ</button>')
            with self.assertRaises(ValidationError):add_item(self.cart,v.pk,1)
        self.assertFalse(self.cart.items.exists())

    def test_stock_check_still_blocks_forged_available_without_bom(self):
        self.rollout()
        v=ProductVariant.objects.get(sku='CF01-360')
        v.is_available=True;v.save(update_fields=['is_available'])
        add_item(self.cart,v.pk,1)
        with self.assertRaises(ValidationError):place_order(self.buyer,self.cart,self.data())
        self.assertEqual(Order.objects.count(),1)
        self.assertEqual(self.cart.items.count(),1)

    def test_forged_web_delivery_rejected_at_form_quote_and_service(self):
        self.rollout()
        self.supply();self.rollout(activate=True)
        add_item(self.cart,ProductVariant.objects.get(sku='CF01-360').pk,3)
        data=self.data();data['fulfillment']='DELIVERY';data['payment_method']='COD'
        from commerce.forms import CheckoutForm
        form=CheckoutForm(data,user=self.buyer)
        self.assertFalse(form.is_valid())
        self.assertIn('fulfillment',form.errors)
        with self.assertRaises(ValidationError):quote_cart(self.cart,self.buyer,'DELIVERY')
        with self.assertRaises(ValidationError):place_order(self.buyer,self.cart,data)
        self.assertEqual(Order.objects.count(),1)

    def test_ready_web_and_pos_use_exact_prices_options_rejected(self):
        self.rollout();self.supply();self.rollout(activate=True)
        for code,name,ml,cost,web,app in MENU:
            v=ProductVariant.objects.get(sku=f'{code}-{ml}')
            add_item(self.cart,v.pk,2)
        quote=quote_cart(self.cart,self.buyer)
        expected=sum(row[4]*2 for row in MENU)
        self.assertEqual((quote['total'],quote['shipping']),(expected,0))
        data=self.data();data['total']=1
        order=place_order(self.buyer,self.cart,data)
        self.assertEqual(order.total,expected)
        for code,name,ml,cost,web,app in MENU:
            v=ProductVariant.objects.get(sku=f'{code}-{ml}')
            for channel,amount in [('COUNTER',web),('APP',app)]:
                manual=manual_order(self.staff,{'channel':channel,'customer_name':'Fixture',
                    'external_reference':str(uuid.uuid4()) if channel=='APP' else '', 'idempotency_key':uuid.uuid4()},
                    [{'variant':v,'quantity':2}])
                self.assertEqual(manual.total,amount*2)
        with self.assertRaises(ValidationError):add_item(self.cart,v.pk,1,['999'])

    def test_price_admin_pairs_web_counter_and_keeps_app(self):
        self.rollout()
        v=ProductVariant.objects.get(sku='CF01-360')
        price=v.prices.get(channel='WEB');price.original_price=29000
        request=RequestFactory().post('/admin/');request.user=self.admin
        admin.site._registry[ChannelPrice].save_model(request,price,None,True)
        self.assertEqual(v.prices.get(channel='COUNTER').original_price,29000)
        self.assertEqual(v.prices.get(channel='APP').original_price,37000)
        self.assertFalse(PriceForm({'variant':v.pk,'channel':'APP','original_price':37000,'sale_price':30000}).is_valid())
        v.is_available=True;v.save()
        v.prices.filter(channel='COUNTER').update(original_price=1)
        with self.assertRaises(ValidationError):add_item(self.cart,v.pk,1)

    def test_cost_admin_denies_staff_even_with_direct_model_permissions(self):
        self.rollout()
        self.staff.user_permissions.add(*Permission.objects.filter(content_type__model='standardcost'))
        for user in [self.buyer,self.staff]:
            self.client.force_login(user)
            self.assertIn(self.client.get('/admin/catalog/standardcost/').status_code,(302,403))
            response=self.client.get('/menu/')
            self.assertNotContains(response,'ingredient_cost')
            self.assertNotContains(response,'standard_cost')
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin/catalog/standardcost/').status_code,200)

    def test_staging_keeps_legacy_available_and_names_unchanged(self):
        names=list(Product.objects.order_by('pk').values_list('name',flat=True))
        call_command('prepare_standard_menu',apply=True,stdout=io.StringIO())
        self.assertEqual(ProductVariant.objects.exclude(size='FIXED').filter(is_available=True).count(),13)
        self.assertFalse(ProductVariant.objects.filter(size='FIXED',is_available=True).exists())
        self.assertEqual(names,list(Product.objects.order_by('pk').values_list('name',flat=True)))

    def test_shortage_prevents_atomic_activation_and_keeps_legacy_open(self):
        call_command('prepare_standard_menu',apply=True,stdout=io.StringIO())
        self.supply()
        StockMovement.objects.create(ingredient=Ingredient.objects.get(sku='TEST-STANDARD-CUP'), delta=-1000,
            reason='ADJUST', actor=self.admin, idempotency_key=uuid.uuid4())
        with self.assertRaises(CommandError): self.rollout(activate=True)
        self.assertEqual(ProductVariant.objects.exclude(size='FIXED').filter(is_available=True).count(),13)
        self.assertFalse(ProductVariant.objects.filter(size='FIXED',is_available=True).exists())

    def test_legacy_mapping_drift_aborts_without_creating_skus(self):
        ProductVariant.objects.filter(sku='CF04-M').update(volume_ml=351)
        with self.assertRaises(CommandError): self.rollout()
        self.assertEqual(ProductVariant.objects.count(),13)
