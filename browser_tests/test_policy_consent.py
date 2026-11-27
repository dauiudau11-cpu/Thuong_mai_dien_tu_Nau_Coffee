"""Real HTTP, CSRF and PostgreSQL on isolated QA. No preview/runtime credentials."""
import os,json
from pathlib import Path
from unittest.mock import patch
from django.test import Client,override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.conf import settings
from django.utils import timezone
from playwright.sync_api import sync_playwright,expect
from tests.test_policy_consent import published_fixture,FLAGS
from tests.test_vouchers_v2 import Helpers,PASSWORD
from commerce.models import Order
from catalog.customer_models import CustomerProfile
from support.models import ConsentEvent,Policy,PolicyRevision
from support import policies
from . import test_journey

@override_settings(**FLAGS)
class PolicyConsentBrowserTests(Helpers,StaticLiveServerTestCase):
    db=test_journey.BrowserJourneyTests.db
    def setUp(self):published_fixture(type(self))
    def cookie(self,user):
        def create():
            c=Client();c.force_login(user);return c.cookies[settings.SESSION_COOKIE_NAME].value
        return self.db(create)
    def test_eleven_policies_registration_checkout_preferences_admin_all_widths(self):
        root=Path(os.environ['NAU_VOUCHER_QA_ROOT'])/'policies';root.mkdir(parents=True,exist_ok=True);rows=[]
        customer_cookie=self.cookie(self.user);admin_cookie=self.cookie(self.admin)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],args=['--no-sandbox'])
            for width in [375,768,1440]:
                ctx=browser.new_context(viewport={'width':width,'height':1000});page=ctx.new_page();errors=[];page.on('pageerror',lambda error:errors.append(type(error).__name__))
                response=page.goto(self.live_server_url+'/policies/');self.assertEqual(response.status,200)
                expect(page.locator('.policy-cards article')).to_have_count(11)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(root/f'{width}-policy-center-footer.png'),full_page=True)
                for slug,title in policies.SECTIONS:
                    self.assertEqual(page.goto(self.live_server_url+'/policies/'+slug+'/').status,200)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'),slug)
                page.goto(self.live_server_url+'/accounts/register/')
                for field in ['full_name','phone','email','username','password1','password2']:expect(page.locator('[name='+field+']')).to_have_count(1)
                expect(page.locator('[name=accept_terms]')).not_to_be_checked();expect(page.locator('[name=marketing]')).not_to_be_checked()
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(root/f'{width}-register.png'),full_page=True)
                values={'full_name':'Khách chính sách','phone':f'09010{width:05d}','email':f'policy-{width}@example.invalid','username':f'policy-{width}','password1':PASSWORD,'password2':PASSWORD}
                for key,value in values.items():page.fill('[name='+key+']',value)
                page.check('[name=accept_terms]');page.get_by_role('button',name='Tạo tài khoản',exact=True).click()
                expect(page.locator('[name=username]')).to_have_count(0)
                profile=self.db(lambda:CustomerProfile.objects.get(user__username=values['username']))
                self.assertEqual(self.db(lambda:ConsentEvent.objects.filter(user_id=profile.user_id,purpose='MARKETING',state='DECLINED').count()),1)
                ctx.close()
                # Existing verified customer: no automatic consent; optional choices may be withdrawn.
                ctx=browser.new_context(viewport={'width':width,'height':1000});ctx.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':customer_cookie,'url':self.live_server_url}]);page=ctx.new_page()
                page.goto(self.live_server_url+'/account/privacy/');page.check('[name=marketing]');page.get_by_role('button',name='Lưu lựa chọn',exact=True).click();expect(page.locator('[name=marketing]')).to_be_checked()
                page.uncheck('[name=marketing]');page.get_by_role('button',name='Lưu lựa chọn',exact=True).click();expect(page.locator('[name=marketing]')).not_to_be_checked()
                self.db(self.cart);page.goto(self.live_server_url+'/checkout/');page.fill('[name=customer_name]','Khách chính sách');page.fill('[name=phone]','0901234567')
                expect(page.locator('[name=accept_order_terms]')).not_to_be_checked();self.assertFalse(page.locator('[name=accept_order_terms]').evaluate('(e)=>e.checkValidity()'))
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(root/f'{width}-checkout.png'),full_page=True)
                page.check('[name=accept_order_terms]');page.check('[name=accept_demo]')
                with patch('commerce.operations.scheduled_slot',return_value=timezone.now()+timezone.timedelta(hours=1)):
                    page.get_by_role('button',name='Đặt đơn mô phỏng',exact=True).click();expect(page.get_by_role('heading',name='THANH TOÁN MÔ PHỎNG',exact=True)).to_be_visible()
                order=self.db(lambda:Order.objects.latest('pk'));self.assertEqual(order.total,28000);self.assertEqual(self.db(lambda:order.policy_events.count()),6)
                ctx.close()
                ctx=browser.new_context(viewport={'width':width,'height':1000});ctx.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':admin_cookie,'url':self.live_server_url}]);page=ctx.new_page()
                policy_id=self.db(lambda:Policy.objects.get(slug='terms').pk)
                page.goto(self.live_server_url+f'/admin/support/policy/{policy_id}/versions/')
                expect(page.locator('#nav-sidebar').get_by_role('link',name='Quản lý chính sách',exact=True,include_hidden=True)).to_have_count(1)
                page.fill('[name=version]',f'qa-browser-{width}');page.fill('[name=title]','Điều khoản sử dụng')
                editor=page.locator('.policy-rich-canvas');expect(editor).to_be_visible();expect(page.get_by_role('toolbar',name='Định dạng nội dung chính sách')).to_be_visible()
                editor.fill('Điều khoản');editor.press('Control+A');page.get_by_role('button',name='Tiêu đề cấp 2').click();editor.press('End');editor.press('Enter');editor.type('Nội dung kiểm thử trên QA.')
                page.get_by_role('button',name='Xem trước',exact=True).click()
                expect(page.get_by_role('heading',name='Xem trước: Điều khoản sử dụng',exact=True)).to_be_visible()
                expect(page.locator('section.policy-reading').get_by_role('heading',name='Điều khoản',exact=True)).to_be_visible()
                page.get_by_role('button',name='Lưu bản nháp',exact=True).click()
                draft=self.db(lambda:PolicyRevision.objects.get(policy_id=policy_id,version=f'qa-browser-{width}'))
                page.goto(self.live_server_url+f'/admin/support/policy/{policy_id}/versions/?draft={draft.pk}')
                page.fill('[name=review_note]','Synthetic QA approval');page.check('[name=reviewed]');page.fill('[name=effective_at]',timezone.localtime().strftime('%Y-%m-%dT%H:%M:%S'))
                page.get_by_role('button',name='Lưu bản nháp',exact=True).click()
                detail=page.locator('details').filter(has_text=f'qa-browser-{width}');detail.locator('summary').click();detail.get_by_role('button',name='Công bố bản đã duyệt',exact=True).click()
                self.assertEqual(self.db(lambda:PolicyRevision.objects.get(pk=draft.pk).status),'PUBLISHED')
                customer_policy=ctx.new_page();self.assertEqual(customer_policy.goto(self.live_server_url+'/policies/terms/').status,200)
                expect(customer_policy.locator('.policy-reading').get_by_role('heading',name='Điều khoản',exact=True)).to_be_visible();customer_policy.close()
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'));page.screenshot(path=str(root/f'{width}-admin.png'),full_page=True)
                self.assertFalse(errors);ctx.close();rows.append({'width':width,'policies':11,'register':True,'marketing_optional':True,'withdraw':True,'checkout':True,'admin_draft_preview_publish':True,'overflow':False})
            browser.close()
        (root/'result.json').write_text(json.dumps({'status':'PASS','viewports':rows},indent=2))
