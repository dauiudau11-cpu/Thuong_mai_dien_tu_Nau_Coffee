"""Issue #2 priorities: real browser checks on isolated PostgreSQL fixtures."""
import os
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright, expect
from commerce.models import Order, StockMovement
from catalog.models import ProductVariant
from . import test_journey


class UIRefinementTests(StaticLiveServerTestCase):
    # Reuse journey setup/helpers without inheriting or rediscovering its tests.
    setUp = test_journey.BrowserJourneyTests.setUp
    login = test_journey.BrowserJourneyTests.login
    db = test_journey.BrowserJourneyTests.db
    customer = test_journey.BrowserJourneyTests.customer
    add_drink = test_journey.BrowserJourneyTests.add_drink
    assert_images_loaded = test_journey.BrowserJourneyTests.assert_images_loaded

    def browser(self, playwright):
        return playwright.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
            headless=True, args=['--no-sandbox'])

    def capture(self, page, name, width):
        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'{name}: {width}px overflow')
        page.screenshot(path=str(self.artifacts / f'ui-{width}-{name}.png'), full_page=True)

    def test_product_preview_options_and_filter_preservation(self):
        from urllib.parse import urlparse, parse_qs
        buyer = self.customer()
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page(viewport={'width':375, 'height':900}, has_touch=True)
            self.login(page, buyer.username)
            page.goto(self.live_server_url + '/menu/?q=Trà&min_price=10000&sort=price_desc&category=tra')
            query = parse_qs(urlparse(page.url).query)
            self.assertEqual(query['q'], ['Trà'])
            self.assertEqual(query['sort'], ['price_desc'])
            self.assertEqual(query['min_price'], ['10000'])
            self.assertEqual(page.locator('.product-card h3').count(), 2)
            target = page.locator('.premium-card-action').first.bounding_box()
            self.assertGreaterEqual(target['height'], 44)
            self.assertGreaterEqual(target['width'], 44)
            page.goto(self.live_server_url + '/products/ca-phe-sua-da/')
            page.locator('[name="quantity"]').fill('2')
            expect(page.locator('.price-preview output')).to_have_text('60.000 đ')
            sugar = page.locator('.purchase-form input[data-kind="SUGAR"]')
            sugar.first.check()
            sugar.last.check()
            expect(sugar.first).not_to_be_checked()
            page.locator('input[data-kind="TOPPING"]').first.check()
            expect(page.locator('.price-preview output')).to_have_text('70.000 đ')
            page.get_by_role('button', name='Thêm vào giỏ', exact=True).click()
            expect(page.locator('.cart-checkout-bar')).to_contain_text('70.000 đ')
            page.locator('.mobile-menu summary').click()
            page.keyboard.press('Escape')
            expect(page.locator('.mobile-menu')).not_to_have_attribute('open', '')
            browser.close()

    def test_manual_dynamic_rows_filter_options_reindex_and_submit(self):
        variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        other = ProductVariant.objects.get(sku='CF01-STANDARD')
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page(viewport={'width':375, 'height':1000})
            self.login(page, self.staff.username)
            page.goto(self.live_server_url + '/dashboard/orders/new-manual/')
            expect(page.locator('.manual-line')).to_have_count(1)
            expect(page.locator('#id_lines-0-options')).to_be_hidden()
            page.locator('#id_lines-0-variant').select_option(str(variant.pk))
            expect(page.locator('#id_lines-0-options')).to_be_visible()
            page.locator('#id_lines-0-quantity').fill('2')
            expect(page.locator('.manual-line-total')).to_contain_text('60.000 đ')
            page.locator('#id_channel').select_option('APP')
            expect(page.locator('.manual-line-total')).to_contain_text('70.000 đ')
            from catalog.models import ProductOption
            allowed = self.db(lambda: set(ProductOption.objects.filter(product=variant.product, is_active=True).values_list('pk', flat=True)))
            visible_ids = page.locator('#id_lines-0-options option:not([disabled])').evaluate_all('(items)=>items.map(i=>Number(i.value))')
            self.assertEqual(set(visible_ids), allowed)
            page.get_by_role('button', name='＋ Thêm món', exact=True).click()
            expect(page.locator('.manual-line')).to_have_count(2)
            page.locator('#id_lines-1-variant').select_option(str(other.pk))
            page.locator('#id_lines-1-quantity').fill('1')
            page.locator('.remove-line').first.click()
            expect(page.locator('#id_lines-0-variant')).to_have_value(str(other.pk))
            expect(page.locator('#id_lines-TOTAL_FORMS')).to_have_value('1')
            page.locator('#id_customer_name').fill('Khách POS UI DEMO')
            page.locator('#id_external_reference').fill('UI-DYNAMIC-APP')
            page.get_by_role('button', name='Tạo đơn', exact=True).click()
            expect(page).to_have_url(self.live_server_url + '/dashboard/orders/')
            order = self.db(lambda: Order.objects.get(external_reference='UI-DYNAMIC-APP'))
            self.assertEqual(order.total, 30000)
            self.assertEqual(self.db(lambda: Order.objects.get(pk=order.pk).payment.status), 'UNPAID')
            browser.close()

    def test_admin_category_crud_uses_only_new_test_fixture(self):
        from catalog.models import Category, Product
        initial_count = Product.objects.count()
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page(viewport={'width':768, 'height':1000})
            self.login(page, self.admin.username)
            page.goto(self.live_server_url + '/admin/catalog/category/add/')
            page.locator('#id_name').fill('Danh mục QA tạm')
            page.locator('#id_slug').fill('qa-ui-only')
            page.locator('input[name="_save"]').click()
            category_id = self.db(lambda: Category.objects.get(slug='qa-ui-only').pk)
            page.goto(self.live_server_url + f'/admin/catalog/category/{category_id}/change/')
            page.locator('#id_name').fill('Danh mục QA sửa')
            page.locator('input[name="_save"]').click()
            self.assertEqual(self.db(lambda: Category.objects.get(pk=category_id).name), 'Danh mục QA sửa')
            page.goto(self.live_server_url + f'/admin/catalog/category/{category_id}/delete/')
            page.locator('input[type="submit"]').click()
            self.assertFalse(self.db(lambda: Category.objects.filter(pk=category_id).exists()))
            self.assertEqual(self.db(lambda: Product.objects.count()), initial_count)
            browser.close()

    def test_empty_checkout_currency_header_and_customer_responsive(self):
        buyer = self.customer()
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page()
            self.login(page, buyer.username)
            for width in [375, 768, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.goto(self.live_server_url + '/checkout/')
                expect(page.get_by_role('heading', name='Giỏ hàng đang trống')).to_be_visible()
                expect(page.get_by_role('button', name='Đặt đơn mô phỏng')).to_have_count(0)
                page.get_by_role('link', name='Chọn đồ uống', exact=True).click()
                expect(page).to_have_url(self.live_server_url + '/menu/')
                expect(page.locator('.premium-menu-tabs')).to_have_count(0)
                price = page.locator('.grid article').filter(has_text='Cà phê sữa đá').locator('.product-card-bottom strong')
                expect(price).to_have_text('30.000 đ')
                self.capture(page, 'menu', width)
                if width < 1000:
                    page.locator('.mobile-menu summary').click()
                    nav = page.get_by_role('navigation', name='Điều hướng điện thoại')
                    expect(nav.get_by_role('link', name='Thực đơn đồ uống')).to_have_attribute('aria-current', 'page')
                    nav.get_by_role('link', name='Giỏ hàng', exact=True).click()
                    expect(page).to_have_url(self.live_server_url + '/cart/')
                page.goto(self.live_server_url + '/checkout/')
                self.capture(page, 'checkout-empty', width)
                page.goto(self.live_server_url + '/')
                self.assert_images_loaded(page)
                self.capture(page, 'home', width)
            self.add_drink(page)
            for width in [375, 768, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.goto(self.live_server_url + '/checkout/')
                expect(page.get_by_role('button', name='Đặt đơn mô phỏng')).to_be_visible()
                expect(page.locator('.summary-total')).to_contain_text('30.000 đ')
                self.capture(page, 'checkout-filled', width)
            page.goto(self.live_server_url + '/cart/')
            page.get_by_role('button', name='Xóa món khỏi giỏ').click()
            page.goto(self.live_server_url + '/checkout/')
            expect(page.get_by_role('heading', name='Giỏ hàng đang trống')).to_be_visible()
            self.assertFalse(self.db(lambda: Order.objects.exists()))
            browser.close()

    def test_inventory_mobile_cards_staff_and_admin_navigation(self):
        before = StockMovement.objects.count()
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page()
            self.login(page, self.staff.username)
            for width in [375, 768, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.goto(self.live_server_url + '/dashboard/inventory/')
                expect(page.locator('caption')).to_have_text('Tồn hiện tại và ngưỡng cảnh báo')
                expect(page.get_by_role('button', name='Lưu biến động')).to_have_count(0)
                expect(page.get_by_role('navigation', name='Điều hướng điều hành').get_by_role('link', name='Báo cáo')).to_have_count(0)
                self.assertGreater(page.locator('td[data-label="Tồn hiện tại"]').count(), 0)
                self.assertEqual(page.locator('tbody tr').first.evaluate('(e)=>getComputedStyle(e).display'),
                    'block' if width == 375 else 'table-row')
                self.capture(page, 'inventory-staff', width)
            admin = browser.new_page()
            self.login(admin, self.admin.username)
            for width in [375, 768, 1440]:
                admin.set_viewport_size({'width': width, 'height': 1000})
                admin.goto(self.live_server_url + '/dashboard/reports/')
                if width <= 1024:
                    admin.get_by_role('button', name='Danh mục quản trị').click()
                expect(admin.get_by_role('navigation', name='Danh mục quản trị').get_by_role('link', name='Báo cáo')).to_have_attribute('aria-current', 'page')
                expect(admin.get_by_text('0 đ', exact=True).first).to_be_visible()
                self.capture(admin, 'reports-admin', width)
                admin.goto(self.live_server_url + '/admin/catalog/product/')
                expect(admin.locator('#result_list tbody tr')).to_have_count(8)
                self.capture(admin, 'catalog-admin', width)
            self.assertEqual(self.db(lambda: StockMovement.objects.count()), before)
            browser.close()

    def test_manual_app_counter_form_keeps_channel_pricing_and_unpaid_state(self):
        variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page()
            self.login(page, self.staff.username)
            for channel, total in [('APP', 70000), ('COUNTER', 60000)]:
                page.goto(self.live_server_url + '/dashboard/orders/new-manual/')
                page.locator('#id_channel').select_option(channel)
                expect(page.locator('#id_external_reference')).to_have_js_property('required', channel == 'APP')
                page.locator('#id_customer_name').fill('Khách kiểm thử UI DEMO')
                page.locator('#id_external_reference').fill('UI-APP-DEMO' if channel == 'APP' else '')
                page.locator('#id_lines-0-variant').select_option(str(variant.pk))
                page.locator('#id_lines-0-quantity').fill('2')
                for width in [375, 768, 1440]:
                    page.set_viewport_size({'width': width, 'height': 1000})
                    self.capture(page, f'manual-{channel.lower()}', width)
                page.get_by_role('button', name='Tạo đơn', exact=True).click()
                expect(page).to_have_url(self.live_server_url + '/dashboard/orders/')
                order = self.db(lambda: Order.objects.get(channel=channel))
                self.assertEqual(order.total, total)
                self.assertEqual(self.db(lambda: Order.objects.get(pk=order.pk).payment.status), 'UNPAID')
                self.assertTrue(self.db(lambda: bool(Order.objects.get(pk=order.pk).items.get().recipe_snapshot)))
            browser.close()

    def test_maps_fallback_blocked_and_without_javascript_at_all_widths(self):
        with sync_playwright() as p:
            browser = self.browser(p)
            context = browser.new_context()
            context.route('https://www.google.com/**', lambda route: route.abort())
            page = context.new_page()
            for width in [375, 768, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.goto(self.live_server_url + '/contact/')
                fallback = page.get_by_role('link', name='Mở bản đồ Nâu Coffee trong cửa sổ mới')
                expect(fallback).to_be_visible()
                expect(fallback).to_have_attribute('rel', 'noopener noreferrer')
                expect(fallback).to_have_attribute('href','https://maps.app.goo.gl/dhm5y4VkBiPHFYJY9?g_st=ic')
                expect(page.locator('.footer-map iframe')).to_have_count(1)
                expect(page.locator('.footer-map iframe')).to_have_attribute('title','Bản đồ chỉ đường đến Nâu Coffee')
                expect(fallback).to_be_visible()
                self.capture(page, 'contact-maps-blocked', width)
            context.close()
            offline = browser.new_context(java_script_enabled=False, viewport={'width': 375, 'height': 1000})
            offline.route('https://www.google.com/**', lambda route: route.abort())
            page = offline.new_page()
            page.goto(self.live_server_url + '/contact/')
            expect(page.get_by_text('457/9 Điện Biên Phủ',exact=False).first).to_be_visible()
            expect(page.get_by_role('link', name='Mở bản đồ Nâu Coffee trong cửa sổ mới')).to_be_visible()
            browser.close()

    def test_reference_pos_cards_select_real_variant_and_config_is_read_only(self):
        variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page(viewport={'width':375, 'height':1000})
            self.login(page, self.staff.username)
            page.goto(self.live_server_url + '/dashboard/orders/new-manual/')
            page.locator(f'.pos-select[data-variant="{variant.pk}"]').click()
            expect(page.locator('#id_lines-0-variant')).to_have_value(str(variant.pk))
            page.locator('#id_lines-0-quantity').fill('2')
            expect(page.locator('.manual-line-total')).to_contain_text('60.000 đ')
            page.locator('#id_channel').select_option('APP')
            expect(page.locator('.manual-line-total')).to_contain_text('70.000 đ')
            page.locator('#id_customer_name').fill('Khách POS cards QA')
            page.locator('#id_external_reference').fill('REFERENCE-CARDS-QA')
            page.get_by_role('button', name='Tạo đơn', exact=True).click()
            expect(page).to_have_url(self.live_server_url + '/dashboard/orders/')
            order = self.db(lambda: Order.objects.get(external_reference='REFERENCE-CARDS-QA'))
            self.assertEqual(order.total, 70000)
            self.assertEqual(self.db(lambda: order.payment.status), 'UNPAID')
            page.goto(self.live_server_url + '/dashboard/kitchen/')
            expect(page.get_by_role('heading', name='Hàng chờ pha chế', exact=True)).to_be_visible()
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            page.get_by_role('button', name='Bắt đầu pha', exact=True).click()
            self.assertEqual(self.db(lambda: Order.objects.get(pk=order.pk).status), 'PREPARING')
            page.goto(self.live_server_url + '/dashboard/kitchen/')
            page.get_by_role('button', name='Sẵn sàng', exact=True).click()
            self.assertEqual(self.db(lambda: Order.objects.get(pk=order.pk).status), 'READY')
            self.assertEqual(self.db(lambda: Order.objects.get(pk=order.pk).payment.status), 'UNPAID')
            self.login(page, self.admin.username)
            page.goto(self.live_server_url + '/dashboard/settings/security/')
            expect(page.get_by_role('navigation', name='Các trang cấu hình').get_by_role('link')).to_have_count(6)
            expect(page.locator('.operations-workspace form')).to_have_count(0)
            browser.close()

    def test_round_two_customer_pages_responsive_and_staff_map_excluded(self):
        with sync_playwright() as p:
            browser = self.browser(p)
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            for width in [375, 768, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                page.goto(self.live_server_url + '/ve-nau/')
                expect(page.get_by_role('heading', name='Một chút Nâu, gần bạn hơn.')).to_be_visible()
                expect(page.locator('.about-row figure img')).to_have_count(3)
                expect(page.get_by_role('link', name='Khám phá thực đơn')).to_be_visible()
                expect(page.locator('.footer-map iframe')).to_have_count(1)
                self.assert_images_loaded(page)
                self.capture(page, 'about-round-two', width)
                page.goto(self.live_server_url + '/contact/')
                expect(page.get_by_role('heading', name='Thông tin liên hệ')).to_be_visible()
                expect(page.get_by_role('link', name='Xem Chính sách & Điều khoản của Nâu Coffee')).to_be_visible()
                self.capture(page, 'contact-round-two', width)
                page.goto(self.live_server_url + '/delivery-partners/')
                expect(page.locator('.partner-heading img')).to_have_count(3)
                self.assert_images_loaded(page)
                self.capture(page, 'partners-round-two', width)
            page.goto(self.live_server_url + '/')
            desktop_nav = page.locator('.desktop-nav')
            expect(desktop_nav.get_by_role('link', name='Liên hệ', exact=True)).to_have_count(0)
            expect(page.locator('.footer-store-identity .social-links a')).to_have_count(3)
            self.login(page, self.staff.username)
            page.goto(self.live_server_url + '/menu/')
            expect(page.locator('.footer-map')).to_have_count(0)
            self.assertEqual(errors, [])
            browser.close()
