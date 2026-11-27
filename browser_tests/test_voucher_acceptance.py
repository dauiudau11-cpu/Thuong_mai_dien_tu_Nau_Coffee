"""Real Chromium HTTP acceptance on attested QA only; fixture identities are .invalid."""
import json
import os
import re
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core import mail
from django.test import override_settings
from django.utils import timezone
from playwright.sync_api import sync_playwright, expect
from catalog.customer_models import CustomerProfile, CounterCustomerLink, CounterConsent
from commerce.models import Order, VoucherUseV2
from commerce import vouchers
from tests.test_vouchers_v2 import Helpers, SETTINGS, fixture
from tests.test_customer_accounts import PASSWORD
from . import test_journey


@override_settings(**SETTINGS)
class VoucherAcceptanceJourney(Helpers, StaticLiveServerTestCase):
    db = test_journey.BrowserJourneyTests.db

    def setUp(self):
        fixture(self.__class__)

    def login(self, page, username):
        page.goto(self.live_server_url+'/accounts/login/')
        page.fill('[name=username]',username);page.fill('[name=password]',PASSWORD)
        page.get_by_role('button',name='Đăng nhập',exact=True).click()
        expect(page).to_have_url(self.live_server_url+'/menu/')

    def checkout(self,page,phone,selected=None):
        page.goto(self.live_server_url+'/products/counter-drink/')
        page.get_by_role('button',name='Thêm vào giỏ',exact=True).click()
        page.goto(self.live_server_url+'/checkout/')
        page.fill('[name=customer_name]','Khách E2E QA');page.fill('[name=phone]',phone)
        page.check('[name=accept_demo]')
        self.assertEqual(page.locator(f'[name=voucher] option[value="{self.expired_id}"]').count(),0)
        if selected==self.public_id:
            page.select_option('[name=voucher]',str(self.minimum_id))
            expect(page.locator('[data-voucher-status]')).to_contain_text('Chưa đạt')
            expect(page.get_by_role('button',name='Đặt đơn mô phỏng',exact=True)).to_be_disabled()
        if selected:page.select_option('[name=voucher]',str(selected))
        expect(page.locator('[data-voucher-status]')).to_contain_text('Ưu đãi đã được áp dụng')
        self.assertEqual(page.locator('[name=voucher_code]').count(),0)
        self.assertEqual(page.get_by_role('button',name='Tính lại giá',exact=True).count(),0)
        self.assertNotIn('Phí nhận tại quán',page.locator('body').inner_text())
        page.get_by_role('button',name='Đặt đơn mô phỏng',exact=True).click()
        expect(page).to_have_url(re.compile('/payments/mock/'))
        page.get_by_role('button',name='Giả lập thành công',exact=True).click()
        expect(page).to_have_url(re.compile('/account/orders/'))

    def test_signup_activation_customer_staff_vouchers_and_guest_app_three_widths(self):
        public=self.voucher();private=self.voucher('PRIVATE')
        self.public_id=public.voucher_id
        self.minimum_id=self.voucher(min_subtotal=999999).voucher_id
        self.expired_id=self.voucher(starts_at=timezone.now()-timedelta(days=2),ends_at=timezone.now()-timedelta(days=1)).voucher_id
        artifacts=Path(os.environ.get('NAU_ACCEPTANCE_QA_ROOT','docs/qa/2026-11-12-voucher-acceptance'))/'browser'
        artifacts.mkdir(parents=True,exist_ok=True);rows=[]
        with patch('commerce.operations.scheduled_slot',return_value=timezone.now()+timedelta(hours=1)),sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],args=['--no-sandbox'])
            for i,width in enumerate((375,768,1440)):
                customer=browser.new_context(viewport={'width':width,'height':1000},locale='vi-VN')
                page=customer.new_page();phone=f'098100000{i}';username=f'e2e-voucher-{i}'
                page.goto(self.live_server_url+'/accounts/register/')
                for name,value in dict(full_name='Khách E2E QA',phone=phone,email=f'voucher{i}@example.invalid',username=username,password1=PASSWORD,password2=PASSWORD).items():page.fill(f'[name={name}]',value)
                page.get_by_role('button',name='Tạo tài khoản',exact=True).click()
                self.assertFalse(self.db(lambda:CustomerProfile.objects.get(user__username=username).user.is_active))
                token=self.db(lambda:re.search(r'#token=([^\s]+)',mail.outbox[-1].body).group(1))
                page.goto(self.live_server_url+'/accounts/activate/#token='+token)
                page.fill('[name=new_password1]',PASSWORD);page.fill('[name=new_password2]',PASSWORD)
                page.get_by_role('button',name='Xác nhận qua email',exact=True).click()
                self.login(page,username)
                uid=self.db(lambda:CustomerProfile.objects.get(user__username=username).user_id)
                self.db(lambda:vouchers.grant_uses(self.admin,private.pk,uid,2,'E2E grant fixture'))
                self.checkout(page,phone,public.voucher_id)
                self.assertEqual(self.db(lambda:VoucherUseV2.objects.filter(user_id=uid,campaign=public).count()),1)
                page.get_by_role('button',name='Yêu cầu hủy trước pha chế',exact=True).click()
                self.assertEqual(self.db(lambda:Order.objects.get(user_id=uid).status),'CANCELLED')
                self.assertEqual(self.db(lambda:VoucherUseV2.objects.filter(user_id=uid,campaign=public).count()),1)
                self.checkout(page,phone,private.voucher_id)
                self.checkout(page,phone)
                self.assertEqual(self.db(lambda:Order.objects.filter(user_id=uid).count()),3)
                page.goto(self.live_server_url+'/account/profile/')
                consent=page.locator('form[action="/account/counter-consent/"]')
                consent.locator('[name=current_password]').fill(PASSWORD);consent.locator('button').click()
                code=page.locator('.consent-code').inner_text()
                staffcontext=browser.new_context(viewport={'width':width,'height':1000},locale='vi-VN');staff=staffcontext.new_page()
                self.login(staff,self.staff.username)
                posts=[]
                staff.on('request',lambda req: posts.append(req.url.split('?')[0].split(self.live_server_url)[-1]) if req.method=='POST' else None)
                staff.goto(self.live_server_url+'/dashboard/customers/create/')
                for name,value in dict(full_name='Khách chờ QA',phone=f'098200000{i}',email=f'pending{i}@example.invalid').items():staff.fill(f'[name={name}]',value)
                staff.get_by_role('button',name='Tạo tài khoản chờ kích hoạt',exact=True).click()
                self.assertFalse(self.db(lambda:CustomerProfile.objects.get(phone=f'+8498200000{i}').user.is_active))
                staff.goto(self.live_server_url+'/dashboard/customers/lookup/')
                staff.fill('[name=phone]',phone);staff.get_by_role('button',name='Tra cứu khách',exact=True).click()
                staff.get_by_role('link',name='Kiểm tra lựa chọn tại POS').click()
                staff.fill('[name=customer_consent]',code);staff.check('[name=confirm_customer]')
                staff.select_option('[name=lines-0-variant]',str(self.variant.pk));staff.fill('[name=lines-0-quantity]','1')
                expect(staff.locator('[data-voucher-status]')).to_contain_text('Ưu đãi đã được áp dụng')
                staff.select_option('[name=voucher]',str(private.voucher_id))
                expect(staff.locator('[data-voucher-total]')).to_have_text('23.000 đ')
                # The legacy POS listener recomputes its local subtotal on change.
                # A duplicate blur/change must keep the confirmed backend discount.
                staff.locator('[name=lines-0-quantity]').dispatch_event('change')
                expect(staff.locator('[data-voucher-total]')).to_have_text('23.000 đ')
                expect(staff.get_by_role('button',name='Tạo đơn',exact=True)).to_be_enabled()
                self.assertFalse(staff.evaluate('document.documentElement.scrollWidth>innerWidth'))
                staff.screenshot(path=str(artifacts/f'{width}-verified-counter.png'),full_page=True,mask=[staff.locator('[name=customer_consent]')])
                invalid=staff.locator('form.manual-order-form').evaluate("form=>[...form.elements].filter(e=>e.willValidate&&!e.validity.valid).map(e=>({name:e.name,message:e.validationMessage}))")
                self.assertEqual(invalid,[])
                staff.get_by_role('button',name='Tạo đơn',exact=True).click()
                try:
                    expect(staff).to_have_url(self.live_server_url+'/dashboard/orders/')
                except AssertionError:
                    detail={'post_paths':posts,'path':staff.url.split(self.live_server_url)[-1], 'submit_state':staff.locator('form.manual-order-form').evaluate("f=>({valid:f.checkValidity(),buttonCount:f.querySelectorAll('button').length,submitButtons:[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Tạo đơn').map(b=>({type:b.type,inForm:b.form===f,disabled:b.disabled})),errors:[...f.querySelectorAll('.errorlist')].map(e=>e.textContent)})")}
                    (artifacts/'submit-diagnostic.json').write_text(json.dumps(detail,ensure_ascii=False,indent=2)+'\n')
                    raise AssertionError('Staff submission did not complete; sanitized diagnostic recorded.') from None
                self.assertEqual(self.db(lambda:CounterCustomerLink.objects.filter(customer_id=uid).count()),1)
                self.assertIsNotNone(self.db(lambda:CounterConsent.objects.get(user_id=uid).used_at))
                for channel in ('COUNTER','APP'):
                    staff.goto(self.live_server_url+'/dashboard/orders/new-manual/')
                    staff.select_option('[name=channel]',channel);staff.fill('[name=customer_name]','Khách vãng lai QA')
                    if channel=='APP':staff.fill('[name=external_reference]',f'QA-APP-{width}')
                    staff.select_option('[name=lines-0-variant]',str(self.variant.pk));staff.fill('[name=lines-0-quantity]','1')
                    expect(staff.locator('[data-voucher-status]')).to_contain_text('Ưu đãi đã được áp dụng' if channel=='COUNTER' else 'không áp dụng voucher')
                    staff.get_by_role('button',name='Tạo đơn',exact=True).click()
                    expect(staff).to_have_url(self.live_server_url+'/dashboard/orders/')
                self.assertEqual(self.db(lambda:Order.objects.filter(user__isnull=True,channel='APP').count()),i+1)
                page.goto(self.live_server_url+'/account/orders/')
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(artifacts/f'{width}-customer-orders.png'),full_page=True)
                rows.append({'width':width,'signup_activation_login':True,'web_public_private_no_voucher':True,'staff_pending_creation':True,'counter_verified_private':True,'guest_counter_app':True,'cancel_no_quota_return':True,'minimum_denied_expired_hidden':True,'overflow':False})
                customer.close();staffcontext.close()
            browser.close()
        (artifacts/'journey.json').write_text(json.dumps(rows,indent=2)+'\n')
