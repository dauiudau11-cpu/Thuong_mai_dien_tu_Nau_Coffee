"""Populated filters must keep Django scalar/pair lookup contracts intact."""
from django.contrib import admin
from django.contrib.admin.filters import AllValuesFieldListFilter
from django.test import TestCase, override_settings, RequestFactory
from support.models import Review, Message
from catalog.models import Product
from catalog.admin_localization import VietnameseAdminMixin
from tests.pickup_compatibility_fixture import load_compatibility_fixture, create_role_user


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class PopulatedAdminFilterTests(TestCase):
    def setUp(self):
        load_compatibility_fixture()
        self.user=create_role_user('admin-filter-qa','ADMIN')
        self.user.is_superuser=True
        self.user.save(update_fields=['is_superuser'])
        from commerce.models import OrderItem
        items=list(OrderItem.objects.select_related('order','variant__product').order_by('pk')[:2])
        self.reviews=[Review.objects.create(item=item,user=item.order.user or self.user,
            product=item.variant.product,rating=rating,body='Đánh giá tổng hợp kiểm thử',status='PENDING')
            for item,rating in zip(items,[1,5])]
        self.client.force_login(self.user)

    def test_populated_review_list_numeric_filter_and_labels(self):
        response=self.client.get('/admin/support/review/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'Đánh giá')
        self.assertContains(response,'Điểm đánh giá')
        cl=response.context['cl']
        rating=next(spec for spec in cl.filter_specs if spec.field.name=='rating')
        self.assertIsInstance(rating,AllValuesFieldListFilter)
        self.assertEqual(list(rating.lookup_choices),[1,5])
        self.assertEqual([choice['display'] for choice in rating.choices(cl)][1:],['1','5'])
        filtered=self.client.get('/admin/support/review/?rating=5')
        self.assertEqual(filtered.status_code,200)
        self.assertEqual(list(filtered.context['cl'].queryset.values_list('rating',flat=True)),[5])
        facets=self.client.get('/admin/support/review/?_facets=1&rating=1')
        self.assertEqual(facets.status_code,200)
        self.assertEqual(list(facets.context['cl'].queryset.values_list('rating',flat=True)),[1])
        self.assertEqual(list(Review.objects.order_by('rating').values_list('rating',flat=True)),[1,5])

    def test_scalar_strings_related_pairs_choices_and_boolean_filters(self):
        class FilterAdmin(VietnameseAdminMixin,admin.ModelAdmin):
            list_filter=['code','category','is_active']
        request=RequestFactory().get('/admin/catalog/product/')
        request.user=self.user
        cl=FilterAdmin(Product,admin.site).get_changelist_instance(request)
        values={spec.field.name:spec for spec in cl.filter_specs}
        self.assertEqual(list(values['code'].lookup_choices),list(Product.objects.order_by('code').values_list('code',flat=True).distinct()))
        self.assertTrue(all(isinstance(value,str) for value in values['code'].lookup_choices))
        self.assertTrue(all(len(pair)==2 for pair in values['category'].lookup_choices))
        for spec in cl.filter_specs:
            for choice in spec.choices(cl):
                self.assertEqual(set(choice),{'selected','query_string','display'})
        from datetime import timedelta
        from django.utils import timezone
        from commerce.models import Voucher
        for code,cap in [('NULL-QA',None),('INT-QA',1000)]:
            Voucher.objects.create(code=code,kind='FIXED',amount=1000,cap=cap,
                starts_at=timezone.now(),ends_at=timezone.now()+timedelta(days=1))
        class NullableFilterAdmin(VietnameseAdminMixin,admin.ModelAdmin):
            list_filter=['cap']
        nullable=NullableFilterAdmin(Voucher,admin.site).get_changelist_instance(request)
        spec=nullable.filter_specs[0]
        self.assertIn(None,list(spec.lookup_choices))
        self.assertIn(1000,list(spec.lookup_choices))
        self.assertTrue(any('cap__isnull=True' in choice['query_string'] for choice in spec.choices(nullable)))
        status=self.client.get('/admin/support/review/?status__exact=PENDING')
        self.assertEqual(status.status_code,200)
        self.assertEqual(status.context['cl'].queryset.count(),2)

    def test_review_message_change_views_and_staff_permissions_remain(self):
        message=Message.objects.create(kind='FEEDBACK',name='Khách kiểm thử',email='qa@example.invalid',subject='Kiểm thử',body='Nội dung kiểm thử')
        self.assertEqual(self.client.get('/admin/support/message/').status_code,200)
        self.assertEqual(self.client.get(f'/admin/support/message/{message.pk}/change/').status_code,200)
        for review in self.reviews:
            self.assertEqual(self.client.get(f'/admin/support/review/{review.pk}/change/').status_code,200)
        self.assertFalse(admin.site._registry[Review].has_add_permission(RequestFactory().get('/')))
        staff=create_role_user('filter-staff-qa','STAFF');self.client.force_login(staff)
        self.assertEqual(self.client.get('/admin/support/review/').status_code,302)

    def test_all_registered_admin_lists_add_and_existing_change_views(self):
        from datetime import timedelta
        from django.utils import timezone
        from catalog.models import ProductImage, ProductOption, ProductVariant, StandardCost
        from catalog.localization import MODEL_NAMES, model_name
        from commerce.models import (Cart, CartItem, Order, Payment, PaymentEvent, OrderStatusHistory,
            Voucher, VoucherRedemption, StoreSettings, Ingredient, OptionRecipeLine, LoyaltyLedger)
        from support.models import Policy
        from django.db import connection
        variant=ProductVariant.objects.first();ingredient=Ingredient.objects.first();order=Order.objects.first()
        option=ProductOption.objects.first() or ProductOption.objects.create(product=variant.product,name='Kiểm thử',kind='SUGAR')
        if not ProductImage.objects.exists():ProductImage.objects.create(product=variant.product,image='qa-placeholder.webp',alt='Ảnh kiểm thử')
        if not StandardCost.objects.exists():StandardCost.objects.create(variant=variant,ingredient_cost=1000)
        if not OptionRecipeLine.objects.exists():OptionRecipeLine.objects.create(option=option,ingredient=ingredient,quantity=1)
        cart=Cart.objects.first() or Cart.objects.create(user=self.user)
        if not CartItem.objects.exists():CartItem.objects.create(cart=cart,variant=variant,quantity=1,config_key='qa')
        voucher=Voucher.objects.first() or Voucher.objects.create(code='FILTER-QA',kind='FIXED',amount=1000,
            starts_at=timezone.now(),ends_at=timezone.now()+timedelta(days=1))
        if not VoucherRedemption.objects.exists():VoucherRedemption.objects.create(voucher=voucher,user=self.user,order=order)
        if not PaymentEvent.objects.exists():PaymentEvent.objects.create(payment=Payment.objects.first(),event_key='qa')
        if not OrderStatusHistory.objects.exists():OrderStatusHistory.objects.create(order=order,to_state=order.status)
        if not LoyaltyLedger.objects.exists():LoyaltyLedger.objects.create(user=self.user,order=order,delta=1,event='EARN')
        if not StoreSettings.objects.exists():StoreSettings.objects.create(name='QA')
        if not Policy.objects.exists():Policy.objects.create(slug='qa',title='Chính sách kiểm thử',body='Nội dung kiểm thử')
        if not Message.objects.exists():Message.objects.create(kind='CONTACT',name='QA',email='qa@example.invalid',subject='Kiểm thử',body='Nội dung')
        models=[model for model in admin.site._registry if model._meta.app_label in MODEL_NAMES]
        self.assertEqual(len(models),28)
        # Once fixtures exist, force every view below to execute under PostgreSQL READ ONLY.
        # A write on a GET becomes a failing SQL error rather than changing fixture data.
        with connection.cursor() as cursor:
            # Resolve deferred fixture FKs before entering the read-only GET phase.
            cursor.execute('SET CONSTRAINTS ALL IMMEDIATE')
            cursor.execute('SET LOCAL transaction_read_only = on')
        for model in models:
            registered=admin.site._registry[model];opts=model._meta
            if opts.label_lower=='support.consentevent':
                self.assertEqual(self.client.get('/admin/support/consentevent/').status_code,403)
                continue  # Feature-OFF audit screen is deliberately unavailable; covered with real events in policy tests.
            obj=model.objects.first()
            self.assertIsNotNone(obj,opts.label)
            path=f'/admin/{opts.app_label}/{opts.model_name}/'
            for url in [path,path+f'{obj.pk}/change/']:
                with self.subTest(url=url):
                    response=self.client.get(url);self.assertEqual(response.status_code,200)
                    self.assertContains(response,model_name(model))
            request=RequestFactory().get(path);request.user=self.user
            if registered.has_add_permission(request):
                with self.subTest(url=path+'add/'):
                    self.assertEqual(self.client.get(path+'add/').status_code,200)
