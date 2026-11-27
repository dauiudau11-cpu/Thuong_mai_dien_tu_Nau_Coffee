"""Real HTTP/CSRF Admin campaign editing at three responsive widths, QA only."""
import json
import os
from pathlib import Path
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from playwright.sync_api import sync_playwright, expect
from tests.test_vouchers_v2 import Helpers, fixture, SETTINGS
from commerce.models import VoucherUseV2
from browser_tests import test_journey


@override_settings(**SETTINGS)
class VoucherAdminHTTPTests(Helpers, StaticLiveServerTestCase):
    db = test_journey.BrowserJourneyTests.db

    def setUp(self):
        self.db(lambda: fixture(self.__class__))

    def test_edit_pause_resume_filters_and_history_over_http(self):
        def prepare():
            campaign=self.voucher(code='ADMINHTTP')
            order=self.place(voucher=campaign.voucher_id)
            return campaign, order, list(VoucherUseV2.objects.values())
        campaign,order,before=self.db(prepare)
        self.client.force_login(self.admin)
        cookie=self.client.cookies[settings.SESSION_COOKIE_NAME].value
        output=Path(os.environ['NAU_VOUCHER_QA_ROOT']);output.mkdir(parents=True,exist_ok=True)
        rows=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],args=['--no-sandbox'])
            for width in (375,768,1440):
                context=browser.new_context(viewport={'width':width,'height':1000},locale='vi-VN')
                context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':cookie,'url':self.live_server_url}])
                page=context.new_page()
                page.goto(self.live_server_url+'/dashboard/vouchers/?q=ADMINHTTP&audience=PUBLIC&status=active')
                page.get_by_role('link',name='ADMINHTTP',exact=True).click()
                expect(page.locator('body')).to_contain_text(str(order.public_code))
                page.uncheck('[name=is_active]')
                page.get_by_role('button',name='Lưu cấu hình',exact=True).click()
                expect(page.locator('[name=is_active]')).not_to_be_checked()
                self.assertFalse(self.db(lambda: type(campaign.voucher).objects.get(pk=campaign.voucher_id).is_active))
                page.check('[name=is_active]')
                page.get_by_role('button',name='Lưu cấu hình',exact=True).click()
                expect(page.locator('[name=is_active]')).to_be_checked()
                overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
                if overflow:
                    page.screenshot(path=str(output/f'{width}-overflow.png'),full_page=True)
                    geometry=page.evaluate("""()=>[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).slice(0,15).map(e=>({tag:e.tagName,id:e.id,class:String(e.className),width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right}))""")
                    (output/f'{width}-overflow.json').write_text(json.dumps(geometry,indent=2))
                self.assertFalse(overflow)
                page.screenshot(path=str(output/f'{width}-admin-http.png'),full_page=True)
                rows.append({'width':width,'http_csrf_edit_pause_resume':True,'history_visible':True,'overflow':False})
                context.close()
            browser.close()
        self.assertEqual(self.db(lambda:list(VoucherUseV2.objects.values())),before)
        self.assertEqual(self.db(lambda:LogEntry.objects.filter(user=self.admin).count()),6)
        (output/'admin-http.json').write_text(json.dumps(rows,indent=2))
