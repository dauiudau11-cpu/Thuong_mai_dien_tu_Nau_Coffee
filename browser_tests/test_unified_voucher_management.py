"""Real HTTP/CSRF unified voucher CRUD; synthetic customers on QA only."""
import json, os, re
from pathlib import Path
from django.test import Client, override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group, Permission
from django.conf import settings
from django.utils import timezone
from playwright.sync_api import sync_playwright, expect
from catalog.customer_models import CustomerProfile
from commerce.models import Voucher, VoucherCampaign, VoucherGrant, VoucherUseV2, Cart, CartItem
from commerce.services import add_item
from commerce.operations import manual_order
from tests.test_vouchers_v2 import fixture, Helpers, SETTINGS
from . import test_journey


@override_settings(**SETTINGS)
class UnifiedVoucherBrowserTests(Helpers,StaticLiveServerTestCase):
    db=test_journey.BrowserJourneyTests.db
    def setUp(self):
        fixture(type(self))
        self.admin.is_staff=True;self.admin.save(update_fields=['is_staff'])
        self.admin.user_permissions.add(*Permission.objects.all())
        self.second=User.objects.create_user('vip-second');self.second.groups.add(Group.objects.get(name='CUSTOMER'))
        CustomerProfile.objects.create(user=self.second,full_name='Khách thứ hai',phone='+84901234568',email='second@example.invalid',origin='PUBLIC',email_verified_at=timezone.now())
        self.other=User.objects.create_user('vip-unselected');self.other.groups.add(Group.objects.get(name='CUSTOMER'))
        CustomerProfile.objects.create(user=self.other,full_name='Khách chưa được cấp',phone='+84901234569',email='other@example.invalid',origin='PUBLIC',email_verified_at=timezone.now())

    def cookie(self,user):
        def get():
            c=Client();c.force_login(user);return c.cookies[settings.SESSION_COOKIE_NAME].value
        return self.db(get)

    def base_form(self,page,code):
        page.fill('[name=code]',code);page.select_option('[name=kind]','FIXED');page.fill('[name=amount]','5000')
        page.fill('[name=min_subtotal]','0');page.fill('[name=max_uses]','30')
        page.fill('[name=starts_at]','2020-01-01T00:00');page.fill('[name=ends_at]','2030-01-01T00:00');page.check('[name=is_active]')

    def test_public_private_multi_recipient_edit_pause_checkout_and_counter(self):
        output=Path(os.environ['NAU_VOUCHER_QA_ROOT'])/'unified';output.mkdir(parents=True,exist_ok=True)
        admin_cookie=self.cookie(self.admin);owner_cookie=self.cookie(self.user);other_cookie=self.cookie(self.other);rows=[]
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],args=['--no-sandbox'])
            for width in [375,768,1440]:
                context=browser.new_context(viewport={'width':width,'height':1000});context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':admin_cookie,'url':self.live_server_url}]);page=context.new_page()
                page.goto(self.live_server_url+'/admin/')
                if width<=1024:page.get_by_role('button',name='Danh mục quản trị').click()
                nav=page.get_by_role('navigation',name='Danh mục quản trị')
                expect(nav.get_by_role('link',name='Mã giảm giá / Voucher',exact=True)).to_have_count(1)
                nav.get_by_role('link',name='Mã giảm giá / Voucher',exact=True).click()
                page.get_by_role('link',name='Tạo voucher',exact=True).click()
                private_code=f'UVIP{width}';self.base_form(page,private_code);page.select_option('[name=audience]','PRIVATE')
                expect(page.locator('[data-private-section]')).to_be_visible()
                for user,query,quota in [(self.user,'counter-customer','2'),(self.second,'vip-second','3')]:
                    page.fill('#voucher-customer-query',query);page.get_by_role('button',name='Tìm khách',exact=True).click()
                    page.locator('[data-customer-results]').get_by_role('button',name=re.compile(query)).click()
                    page.locator(f'[data-customer-id="{user.pk}"] input[type=number]').fill(quota)
                page.fill('[name=reason]','Cấp VIP theo yêu cầu khách')
                page.get_by_role('button',name='Tạo voucher',exact=True).click();expect(page.get_by_role('heading',name=private_code,exact=True)).to_be_visible()
                private=self.db(lambda:Voucher.objects.get(code=private_code))
                self.assertEqual(self.db(lambda:list(VoucherGrant.objects.filter(campaign__voucher=private).order_by('user_id').values_list('allocated',flat=True))),[2,3])
                # Granted Customer sees it; an equally verified but unselected Customer does not.
                def carts():
                    for user in [self.user,self.other]:
                        cart,_=Cart.objects.get_or_create(user=user);CartItem.objects.filter(cart=cart).delete();add_item(cart,self.variant.pk,1)
                self.db(carts)
                for cookie,visible in [(owner_cookie,True),(other_cookie,False)]:
                    ctx=browser.new_context(viewport={'width':width,'height':1000});ctx.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':cookie,'url':self.live_server_url}]);p=ctx.new_page();p.goto(self.live_server_url+'/checkout/')
                    options=p.locator('[name=voucher] option').all_text_contents()
                    self.assertEqual(any(private_code in label for label in options),visible);ctx.close()
                # Existing verified Staff consent/selection rules remain the only COUNTER path.
                counter=self.db(lambda:manual_order(self.staff,self.counter_data(voucher=private.pk),self.lines()))
                self.assertEqual(counter.discount,5000);self.assertEqual(counter.total,23000)
                page.reload();page.get_by_role('button',name='Dọn các hàng chưa chọn',exact=True).click()
                page.fill('#voucher-customer-query','counter-customer');page.get_by_role('button',name='Tìm khách',exact=True).click();page.locator('[data-customer-results]').get_by_role('button',name=re.compile('counter-customer')).click()
                expect(page.locator(f'[data-customer-id="{self.user.pk}"] input[type=number]')).to_have_value('2')
                page.locator(f'[data-customer-id="{self.user.pk}"] input[type=number]').fill('4')
                page.fill('[name=reason]','Điều chỉnh lượt theo yêu cầu');page.get_by_role('button',name='Lưu cấu hình',exact=True).click()
                expect(page.get_by_role('heading',name='Nhật ký cấp và điều chỉnh lượt')).to_be_visible()
                page.uncheck('[name=is_active]');page.get_by_role('button',name='Lưu cấu hình',exact=True).click();expect(page.locator('[name=is_active]')).not_to_be_checked()
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(output/f'{width}-private.png'),full_page=True)
                page.goto(self.live_server_url+'/admin/commerce/voucher/add/');public_code=f'UPUB{width}';self.base_form(page,public_code)
                # Toggling to PUBLIC must not accidentally submit stale private recipients.
                page.select_option('[name=audience]','PRIVATE');page.fill('#voucher-customer-query','counter-customer');page.get_by_role('button',name='Tìm khách',exact=True).click();page.locator('[data-customer-results]').get_by_role('button',name=re.compile('counter-customer')).click()
                page.select_option('[name=audience]','PUBLIC');expect(page.locator('[data-private-section]')).not_to_be_visible()
                page.get_by_role('button',name='Tạo voucher',exact=True).click();expect(page.get_by_role('heading',name=public_code,exact=True)).to_be_visible()
                public=self.db(lambda:Voucher.objects.get(code=public_code));self.assertEqual(self.db(lambda:VoucherGrant.objects.filter(campaign__voucher=public).count()),0)
                # Actual Customer checkout uses the newly created public voucher and consumes once.
                ctx=browser.new_context(viewport={'width':width,'height':1000});ctx.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':owner_cookie,'url':self.live_server_url}]);customer=ctx.new_page();customer.goto(self.live_server_url+'/checkout/')
                customer.fill('[name=customer_name]','Khách Quầy');customer.fill('[name=phone]','0901234567');customer.select_option('[name=voucher]',str(public.pk));customer.check('[name=accept_demo]')
                expect(customer.locator('.summary-total')).to_contain_text('23.000')
                customer.get_by_role('button',name='Đặt đơn mô phỏng',exact=True).click();expect(customer.get_by_role('heading',name='THANH TOÁN MÔ PHỎNG',exact=True)).to_be_visible()
                self.assertEqual(self.db(lambda:VoucherUseV2.objects.filter(campaign__voucher=public,user=self.user).count()),1)
                ctx.close();context.close();rows.append({'width':width,'create_private_two_customers':True,'edit_audit_pause':True,'private_visibility':True,'counter_verified_consent':True,'public_checkout':True,'scope_toggle':True})
            browser.close()
        (output/'result.json').write_text(json.dumps({'status':'PASS','screens':rows},indent=2))
