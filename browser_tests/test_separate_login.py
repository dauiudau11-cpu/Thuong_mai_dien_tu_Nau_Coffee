import os
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import expect, sync_playwright


class SeparateLoginBrowserTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for name in ('CUSTOMER', 'STAFF', 'ADMIN'):
            Group.objects.get_or_create(name=name)
        cls.staff = User.objects.create_user('browser-gateway-staff', password='Browser-gateway-728!')
        cls.staff.groups.add(Group.objects.get(name='STAFF'))

    def test_customer_and_internal_gateways_at_all_widths(self):
        output = Path('docs/qa/2026-11-20-separate-login')
        output.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'])
            page = browser.new_page(locale='vi-VN')
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            for width in (375, 768, 1440):
                page.set_viewport_size({'width':width, 'height':1000})
                page.goto(self.live_server_url + '/internal/login/')
                expect(page.get_by_role('heading', name='Đăng nhập nội bộ')).to_be_visible()
                expect(page.locator('footer')).to_have_count(0)
                expect(page.locator('.footer-map')).to_have_count(0)
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.screenshot(path=str(output / f'{width}-internal-login.png'), full_page=True)
                page.goto(self.live_server_url + '/accounts/login/')
                expect(page.get_by_role('heading', name='Mừng bạn ghé lại.')).to_be_visible()
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.screenshot(path=str(output / f'{width}-customer-login.png'), full_page=True)
            page.goto(self.live_server_url + '/internal/login/')
            page.locator('#id_username').fill(self.staff.username)
            page.locator('#id_password').fill('Browser-gateway-728!')
            page.get_by_role('button', name='Đăng nhập').click()
            expect(page).to_have_url(self.live_server_url + '/dashboard/kitchen/')
            page.goto(self.live_server_url + '/')
            expect(page.get_by_role('link', name='Trở về trang điều hành').first).to_be_visible()
            expect(page.locator('[aria-label="Giỏ hàng"]')).to_have_count(0)
            self.assertFalse(errors, errors)
            browser.close()
