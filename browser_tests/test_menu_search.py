import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from playwright.sync_api import expect, sync_playwright

from catalog.models import Category, ChannelPrice, Product, ProductVariant


@override_settings(NAU_STANDARD_MENU_ENABLED=False)
class MenuSearchBrowserTests(StaticLiveServerTestCase):
    def setUp(self):
        category = Category.objects.create(name='Cà phê', slug='ca-phe')
        for code, name, price in (
            ('CF01', 'Cà phê sữa', 39000), ('CF02', 'Bạc xỉu', 35000),
        ):
            product = Product.objects.create(
                code=code, name=name, slug=code.lower(), category=category,
            )
            variant = ProductVariant.objects.create(
                product=product, sku=f'{code}-FIXED', size='FIXED', volume_ml=360,
            )
            ChannelPrice.objects.create(variant=variant, channel='WEB', original_price=price)

    def test_ajax_enter_clear_history_reload_and_responsive(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'],
            )
            page = browser.new_page(locale='vi-VN')
            for width in (375, 768, 1440):
                page.set_viewport_size({'width': width, 'height': 900})
                page.goto(self.live_server_url + '/menu/')
                search = page.get_by_label('Tìm kiếm thức uống')
                if not search.is_visible():
                    page.locator('.menu-filter-disclosure summary').click()
                expect(search).to_be_visible()
                search.fill('bac xiu')
                page.wait_for_timeout(500)
                self.assertIn('q=bac+xiu', page.url, page.locator('.menu-filter-status').text_content())
                expect(page.locator('.product-card h3')).to_have_text('Bạc xỉu')
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))

            page.get_by_label('Xóa từ khóa tìm kiếm').click()
            expect(page.locator('.product-card h3')).to_have_count(2)
            page.get_by_label('Tìm kiếm thức uống').fill('ca phe sua')
            page.get_by_label('Tìm kiếm thức uống').press('Enter')
            page.wait_for_url('**/menu/?q=ca+phe+sua')
            expect(page.locator('.product-card h3')).to_have_text('Cà phê sữa')
            page.reload()
            expect(page.get_by_label('Tìm kiếm thức uống')).to_have_value('ca phe sua')
            page.go_back()
            expect(page.get_by_label('Tìm kiếm thức uống')).to_have_value('')
            expect(page.locator('.product-card h3')).to_have_count(2)
            page.go_forward()
            expect(page.locator('.product-card h3')).to_have_count(1)
            expect(page.locator('.product-card h3')).to_have_text('Cà phê sữa')
            browser.close()
