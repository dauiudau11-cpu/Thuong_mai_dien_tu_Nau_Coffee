"""Chromium -> intercepted Django client, independent QA only; no extra listener."""
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit, unquote
from unittest.mock import patch
from django.conf import settings
from django.test import TransactionTestCase, override_settings
from playwright.sync_api import sync_playwright, expect
from tests.test_vouchers_v2 import SETTINGS, Helpers, fixture
from commerce import vouchers

@override_settings(**SETTINGS)
class VoucherResponsiveTests(Helpers, TransactionTestCase):

    def setUp(self):
        fixture(self.__class__)

    def test_customer_counter_and_admin_responsive_and_live_totals(self):
        campaign = self.voucher()
        private = self.voucher('PRIVATE')
        vouchers.grant_uses(self.admin, private.pk, self.user.pk, 2, 'Responsive fixture')
        self.cart()
        root = Path(settings.BASE_DIR) / 'static'
        artifacts = Path(os.getenv('NAU_VOUCHER_QA_ROOT', 'docs/qa/2026-11-12-vouchers/browser'))
        artifacts.mkdir(parents=True, exist_ok=True)
        rows = []
        with patch.dict(os.environ, {'DJANGO_ALLOW_ASYNC_UNSAFE': 'true'}), sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'), args=['--no-sandbox'])
            page = browser.new_page(locale='vi-VN')

            def intercept(route):
                request = route.request
                path = unquote(urlsplit(request.url).path)
                if path.startswith('/static/'):
                    file = (root / path[len('/static/'):]).resolve()
                    if file.is_relative_to(root.resolve()) and file.is_file():
                        route.fulfill(status=200, content_type=mimetypes.guess_type(str(file))[0] or 'application/octet-stream', body=file.read_bytes())
                    else:
                        route.abort()
                elif path.startswith('/dashboard/vouchers/') or path in ('/checkout/', '/checkout/voucher-quote/', '/dashboard/orders/new-manual/', '/dashboard/orders/voucher-quote/', '/dashboard/vouchers/'):
                    response = self.client.generic(request.method, path, data=request.post_data_buffer or b'', content_type=request.headers.get('content-type', ''))
                    route.fulfill(status=response.status_code, content_type=response.get('Content-Type', 'text/html'), headers={'Location': response['Location']} if response.has_header('Location') else {}, body=response.content)
                else:
                    route.abort()
            page.route('**/*', intercept)
            for width in (375, 768, 1440):
                page.set_viewport_size({'width': width, 'height': 1000})
                self.client.force_login(self.user)
                page.goto('http://testserver/checkout/')
                page.locator('[data-voucher-status]').filter(has_text='Ưu đãi đã được áp dụng').wait_for()
                page.select_option('[name=voucher]', str(campaign.voucher_id))
                page.wait_for_function("document.querySelector('[data-voucher-total]').textContent==='23.000 đ'")
                self.assertEqual(page.locator('button:has-text("Tính lại giá")').count(), 0)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(artifacts / f'{width}-checkout.png'), full_page=True)
                rows.append({'width': width, 'page': 'checkout', 'total': 23000, 'overflow': False})
                self.client.force_login(self.staff)
                self.client.post('/dashboard/customers/lookup/', {'phone': '0901234567'})
                from catalog import customer_accounts as accounts
                from tests.test_customer_accounts import PASSWORD
                code = accounts.issue_counter_consent(self.user, PASSWORD)
                page.goto('http://testserver/dashboard/orders/new-manual/')
                page.fill('[name=customer_consent]', code)
                page.check('[name=confirm_customer]')
                page.select_option('[name=lines-0-variant]', str(self.variant.pk))
                page.fill('[name=lines-0-quantity]', '1')
                page.locator('[data-voucher-status]').filter(has_text='Ưu đãi đã được áp dụng').wait_for()
                page.select_option('[name=voucher]', str(private.voucher_id))
                page.wait_for_function("document.querySelector('[data-voucher-total]').textContent==='23.000 đ'")
                page.fill('[name=lines-0-quantity]', '2')
                page.wait_for_function("document.querySelector('[data-voucher-total]').textContent==='51.000 đ'")
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(artifacts / f'{width}-counter.png'), full_page=True, mask=[page.locator('[name=customer_consent]')])
                page.select_option('[name=channel]', 'APP')
                page.wait_for_function("document.querySelector('[name=voucher]').disabled")
                rows.append({'width': width, 'page': 'counter', 'quantity_changed_total': 51000, 'overflow': False})
                self.client.force_login(self.admin)
                page.goto('http://testserver/dashboard/vouchers/')
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(artifacts / f'{width}-admin.png'), full_page=True)
                rows.append({'width': width, 'page': 'admin', 'overflow': False})
                page.goto(f'http://testserver/dashboard/vouchers/{private.pk}/')
                page.get_by_role('heading', name=private.voucher.code, exact=True).wait_for()
                expect(page.locator('[name=audience]')).to_have_value('PRIVATE')
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(artifacts / f'{width}-admin-detail.png'), full_page=True)
                rows.append({'width': width, 'page': 'admin-detail', 'overflow': False})
            browser.close()
        (artifacts / 'responsive.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
