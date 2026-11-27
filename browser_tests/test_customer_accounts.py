"""Rendered UI only: Chromium receives HTML from an in-memory SQLite test client.
No TCP listener, preview connection, or real customer data is used.
"""
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from playwright.sync_api import sync_playwright
from catalog import customer_accounts as accounts
from tests.test_customer_accounts import EMAIL_SETTINGS, PASSWORD


@override_settings(**EMAIL_SETTINGS)
class CustomerAccountsResponsiveTests(TestCase):
    def test_account_and_staff_pages_at_three_widths(self):
        for name in ('CUSTOMER', 'STAFF'):Group.objects.create(name=name)
        profile=accounts.create_customer(dict(full_name='Khách kiểm thử giao diện',phone='0901234567',
            email='responsive@example.invalid',username='responsive-fixture',password1=PASSWORD))
        accounts.activate(accounts.token_for(profile),PASSWORD,PASSWORD)
        profile.user.refresh_from_db()
        staff=User.objects.create_user('responsive-staff',password=PASSWORD)
        staff.groups.add(Group.objects.get(name='STAFF'))
        html={}
        for path in ('/accounts/register/','/accounts/activate/','/accounts/activation/resend/'):
            response=self.client.get(path);self.assertEqual(response.status_code,200)
            html[path]=response.content.decode()
        response=self.client.post('/accounts/register/',dict(full_name='Khách mới',phone='0901234568',
            email='pending@example.invalid',username='pending-responsive',password1=PASSWORD,password2=PASSWORD))
        html['/fixture/pending/']=response.content.decode()
        self.client.force_login(profile.user)
        html['/account/profile/']=self.client.get('/account/profile/').content.decode()
        html['/account/counter-consent/']=self.client.post('/account/counter-consent/',{'current_password':PASSWORD}).content.decode()
        self.client.force_login(staff)
        for path in ('/dashboard/customers/lookup/','/dashboard/customers/create/','/dashboard/orders/new-manual/'):
            response=(self.client.post(path,{'phone':'0901234567'}) if path.endswith('lookup/') else self.client.get(path))
            self.assertEqual(response.status_code,200)
            html[path]=response.content.decode()
        root=Path(settings.BASE_DIR)/'static'
        artifacts=Path(os.getenv('NAU_CUSTOMER_QA_ROOT','docs/qa/2026-11-12-customer-accounts'));artifacts.mkdir(parents=True,exist_ok=True)
        rows=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
            page=browser.new_page(locale='vi-VN')
            def intercept(route):
                path=unquote(urlsplit(route.request.url).path)
                if path in html:route.fulfill(status=200,content_type='text/html; charset=utf-8',body=html[path])
                elif path.startswith('/static/'):
                    file=(root/path[len('/static/'):]).resolve()
                    if file.is_relative_to(root.resolve()) and file.is_file():
                        route.fulfill(status=200,content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream',body=file.read_bytes())
                    else:route.abort()
                else:route.abort()
            page.route('**/*',intercept)
            for width in (375,768,1440):
                page.set_viewport_size({'width':width,'height':1000})
                for index,path in enumerate(html):
                    response=page.goto('http://testserver'+path,wait_until='load')
                    page.evaluate('async()=>await document.fonts.ready')
                    overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    self.assertFalse(overflow,(width,path))
                    font=page.locator('body').evaluate('e=>getComputedStyle(e).fontFamily')
                    self.assertIn('Be Vietnam Pro',font)
                    name=f'{width}-{index:02}.png'
                    page.screenshot(path=str(artifacts/name),full_page=True,mask=[page.locator('.consent-code')])
                    rows.append({'width':width,'path':path,'status':response.status,'overflow':overflow,'body_font':font,'screenshot':name})
            page.goto('http://testserver/accounts/activate/#token=fixture-not-a-real-token',wait_until='load')
            self.assertEqual(page.locator('input[name=token]').input_value(),'fixture-not-a-real-token')
            self.assertNotIn('#',page.url)
            browser.close()
        (artifacts/'responsive.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
