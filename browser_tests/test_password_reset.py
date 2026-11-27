"""Chromium HTTP recovery on guarded PostgreSQL QA; tokens never persisted in evidence."""
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core import mail
from django.test import override_settings
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright,expect
from catalog import customer_accounts as accounts
from django.contrib.auth.models import User
from tests import test_password_reset as reset_tests
from tests import test_customer_accounts as phase1
from . import test_journey


@override_settings(**reset_tests.SETTINGS)
class PasswordResetBrowserTests(StaticLiveServerTestCase):
    db=test_journey.BrowserJourneyTests.db

    def setUp(self):
        reset_tests.fixture(self.__class__)

    def test_customer_can_recover_and_login_at_three_widths_without_url_token_leak(self):
        output=Path(os.environ.get('NAU_RESET_QA_ROOT','docs/qa/2026-11-12-password-reset'))/'browser'
        output.mkdir(parents=True,exist_ok=True);rows=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],args=['--no-sandbox'])
            for i,width in enumerate((375,768,1440)):
                def create():
                    profile=accounts.create_customer(dict(full_name='Khách Khôi Phục',phone=f'098300000{i}',email=f'reset{i}@example.invalid',username=f'reset-browser-{i}',password1=phase1.PASSWORD))
                    accounts.activate(accounts.token_for(profile),phase1.PASSWORD,phase1.PASSWORD)
                    return profile.user_id
                uid=self.db(create);new=f'Reset-browser-{width}-Safe-924!'
                context=browser.new_context(viewport={'width':width,'height':1000},locale='vi-VN');page=context.new_page()
                requests=[];page.on('request',lambda request:requests.append(request.url))
                page.goto(self.live_server_url+'/accounts/login/')
                page.get_by_role('link',name='Quên mật khẩu?',exact=True).click()
                expect(page).to_have_url(self.live_server_url+reset_tests.REQUEST)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(output/f'{width}-request.png'),full_page=True)
                page.fill('[name=email]',f'reset{i}@example.invalid')
                page.get_by_role('button',name='Yêu cầu đặt lại mật khẩu',exact=True).click()
                expect(page).to_have_url(self.live_server_url+reset_tests.DONE)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(output/f'{width}-done.png'),full_page=True)
                email=self.db(lambda:mail.outbox[-1])
                link=re.search(r'https://\S+',email.body)[0];fragment=urlsplit(link).fragment
                token=fragment.split('&token=',1)[1]
                page.goto(self.live_server_url+reset_tests.EXCHANGE+'#'+fragment)
                expect(page).to_have_url(self.live_server_url+reset_tests.CONFIRM)
                self.assertNotIn('#',page.url)
                self.assertFalse(any(token in url for url in requests))
                page.fill('[name=new_password1]','123');page.fill('[name=new_password2]','123')
                page.get_by_role('button',name='Lưu mật khẩu mới',exact=True).click()
                expect(page.locator('.errorlist').first).to_be_visible()
                self.assertNotIn('This password',page.locator('body').inner_text())
                page.fill('[name=new_password1]',new);page.fill('[name=new_password2]',new)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(output/f'{width}-new-password.png'),full_page=True,mask=[page.locator('[type=password]')])
                page.get_by_role('button',name='Lưu mật khẩu mới',exact=True).click()
                expect(page).to_have_url(self.live_server_url+reset_tests.COMPLETE)
                self.assertTrue(self.db(lambda:User.objects.get(pk=uid).check_password(new)))
                self.assertFalse(self.db(lambda:User.objects.get(pk=uid).check_password(phase1.PASSWORD)))
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(output/f'{width}-complete.png'),full_page=True)
                page.goto(self.live_server_url+reset_tests.EXCHANGE+'#'+fragment)
                expect(page.get_by_role('heading',name='Liên kết không còn hợp lệ.',exact=True)).to_be_visible()
                page.goto(self.live_server_url+'/accounts/login/')
                page.fill('[name=username]',f'reset-browser-{i}');page.fill('[name=password]',phase1.PASSWORD)
                page.get_by_role('button',name='Đăng nhập',exact=True).click()
                expect(page.locator('.errorlist').first).to_be_visible()
                page.fill('[name=password]',new);page.get_by_role('button',name='Đăng nhập',exact=True).click()
                expect(page).to_have_url(self.live_server_url+'/menu/')
                self.assertFalse(any(token in url for url in requests))
                rows.append({'width':width,'screens':4,'overflow':False,'old_password_denied':True,'new_password_login':True,'token_reuse_denied':True,'token_in_network_urls':False,'request_count':len(requests)})
                context.close()
            browser.close()
        (output/'journey.json').write_text(json.dumps(rows,indent=2)+'\n')

    def test_branded_reset_email_renders_offline_at_three_widths(self):
        output=Path(os.environ.get('NAU_RESET_QA_ROOT','docs/qa/2026-11-12-password-reset'))/'browser'
        output.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],args=['--no-sandbox'])
            page=browser.new_page();external=[]
            page.route('**/*',lambda route:(external.append('blocked'),route.abort()))
            for width in (375,768,1440):
                page.set_viewport_size({'width':width,'height':1000})
                page.set_content(render_to_string('emails/customer_password_reset.html',{'reset_url':'https://coffee.example.invalid/accounts/password/reset/confirm/#uid=fixture&token='+'not-real'*24,'expiry_minutes':60}))
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                self.assertIn('60 phút',page.locator('body').inner_text())
                page.screenshot(path=str(output/f'{width}-email.png'),full_page=True,mask=[page.locator('a').last])
            self.assertEqual(external,[]);browser.close()
