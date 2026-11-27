"""Presentation changes must preserve field keys, stored codes and admin permissions."""
from datetime import timedelta
from django.contrib import admin
from django.contrib.auth.models import User, Group, Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from commerce.models import Voucher, Order, Payment
from catalog.localization import FIELD_LABELS, MODEL_NAMES, model_name
from catalog.templatetags.nau_ui import vi_state


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class LocalizationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('localization-qa', 'qa@example.invalid', 'QA-only-testing-823!')
        self.client.force_login(self.admin)

    def test_every_registered_admin_list_and_form_renders(self):
        for model, registered in admin.site._registry.items():
            opts = model._meta
            if opts.app_label not in MODEL_NAMES:
                continue
            url = f'/admin/{opts.app_label}/{opts.model_name}/'
            with self.subTest(model=opts.label):
                response = self.client.get(url)
                if opts.label_lower=='support.consentevent':
                    self.assertEqual(response.status_code,403)
                    continue  # New audit UI must stay unavailable while its feature is OFF.
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, model_name(model))
                if registered.has_add_permission(response.wsgi_request):
                    form = self.client.get(url + 'add/')
                    self.assertEqual(form.status_code, 200)
                    self.assertContains(form, 'Thêm ' + model_name(model).lower())
                    for name, field in form.context['adminform'].form.fields.items():
                        if name in FIELD_LABELS:
                            self.assertEqual(field.label, FIELD_LABELS[name])

    def test_voucher_crud_validation_search_filter_keep_values(self):
        now = timezone.localtime()
        data = {'code':'VI-QA','kind':'FIXED','amount':'25000','cap':'','min_subtotal':'100000',
                'max_uses':'5','per_user_limit':'1','starts_at_0':now.strftime('%Y-%m-%d'),
                'starts_at_1':'00:00:00','ends_at_0':(now+timedelta(days=3)).strftime('%Y-%m-%d'),
                'ends_at_1':'23:00:00','is_active':'on','_save':'Lưu'}
        bad=self.client.post('/admin/commerce/voucher/add/',dict(data,amount='0'))
        self.assertEqual(bad.status_code,200)
        self.assertTrue(bad.context['adminform'].form.errors)
        self.assertFalse(Voucher.objects.filter(code='VI-QA').exists())
        response=self.client.post('/admin/commerce/voucher/add/',data)
        self.assertEqual(response.status_code,302)
        voucher=Voucher.objects.get(code='VI-QA');self.assertEqual(voucher.kind,'FIXED');self.assertEqual(voucher.amount,25000)
        response=self.client.get('/admin/commerce/voucher/?q=VI-QA&kind__exact=FIXED')
        self.assertContains(response,'VI-QA');self.assertContains(response,'Mã giảm giá')
        data['amount']='26000';self.assertEqual(self.client.post(f'/admin/commerce/voucher/{voucher.pk}/change/',data).status_code,302)
        voucher.refresh_from_db();self.assertEqual(voucher.amount,26000)
        self.assertEqual(self.client.get(f'/admin/commerce/voucher/{voucher.pk}/delete/').status_code,200)

    def test_translating_history_does_not_change_model_metadata_or_codes(self):
        self.assertEqual(vi_state('PREPARING'),'Đang pha chế')
        self.assertEqual(vi_state('READY'),'Sẵn sàng nhận')
        self.assertEqual(Order.Status.PREPARING.value,'PREPARING')
        self.assertEqual(Payment.Method.MOCK_ONLINE.value,'MOCK_ONLINE')
        before=Voucher._meta.verbose_name
        self.client.get('/admin/commerce/voucher/')
        self.client.get('/admin/commerce/voucher/add/')
        self.assertEqual(Voucher._meta.verbose_name,before)
        self.assertEqual(Voucher._meta.get_field('min_subtotal').verbose_name,'min subtotal')

    def test_staff_cannot_gain_admin_permissions_through_labels(self):
        user=User.objects.create_user('vi-staff',password='QA-only-testing-823!',is_staff=True)
        group,_=Group.objects.get_or_create(name='STAFF');user.groups.add(group)
        self.client.force_login(user)
        self.assertEqual(self.client.get('/admin/commerce/voucher/').status_code,302)
        self.assertEqual(group.name,'STAFF')

    def test_readonly_order_and_payment_show_translated_codes(self):
        from commerce.models import OrderStatusHistory
        import uuid
        order=Order.objects.create(user=self.admin,channel='WEB',fulfillment='PICKUP',
            customer_name='Khách kiểm thử',subtotal=100,total=100,status='PREPARING',idempotency_key=uuid.uuid4())
        payment=Payment.objects.create(order=order,method='MOCK_ONLINE',status='PAID',amount=100)
        history=OrderStatusHistory.objects.create(order=order,from_state='CONFIRMED',to_state='PREPARING')
        for model,obj in [('order',order),('payment',payment),('orderstatushistory',history)]:
            response=self.client.get(f'/admin/commerce/{model}/{obj.pk}/change/')
            self.assertEqual(response.status_code,200)
            self.assertNotContains(response,'>PREPARING<')
            self.assertNotContains(response,'>MOCK_ONLINE<')
            self.assertNotContains(response,'>CONFIRMED<')
