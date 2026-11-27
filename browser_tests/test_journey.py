"""Real Chromium against Django live server and dedicated PostgreSQL test DB."""
import os
from pathlib import Path
from datetime import timedelta
from django.utils import timezone
from concurrent.futures import ThreadPoolExecutor
from django.db import connections
from django.contrib.auth.models import User, Group
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from playwright.sync_api import sync_playwright, expect
from commerce.models import Order, LoyaltyLedger, Ingredient
from commerce.operations import adjust_stock, balance
import uuid
from catalog.models import ProductVariant
from support.models import Review, Message


def accept_staff_dialog(dialog):
    dialog.accept()


def process_staff_pickup(page, code, actions=None):
    page.goto(page.url.split('/dashboard/')[0] + '/dashboard/kitchen/')
    card = page.locator(f'[data-code="{code}"]')
    for label, state in (actions or [('Bắt đầu pha chế','PREPARING'),('Pha xong','PICKUP_WAITING'),('Đã giao khách','COMPLETED')]):
        if state == 'COMPLETED':
            page.once('dialog', accept_staff_dialog)
        card.get_by_role('button', name=label, exact=True).click()
        expect(card).to_have_attribute('data-status', state)


class BrowserJourneyTests(StaticLiveServerTestCase):
    def customer(self):
        user = User.objects.create_user('browser-returning-customer', password='Browser-testing-823!')
        user.groups.add(Group.objects.get(name='CUSTOMER'))
        return user

    def fill_checkout(self, page, method='MOCK_ONLINE'):
        page.goto(self.live_server_url + '/checkout/')
        page.locator('#id_customer_name').fill('Khách browser DEMO')
        page.locator('#id_phone').fill('0900000000')
        page.locator('#id_payment_method').select_option(method)
        page.locator('#id_accept_demo').check()

    def add_drink(self, page, quantity=1):
        page.goto(self.live_server_url + '/products/ca-phe-sua-da/')
        page.locator('input[name="quantity"]').fill(str(quantity))
        page.get_by_role('button', name='Thêm vào giỏ').click()

    def db(self, action):
        # Playwright's sync API owns an event loop; keep Django ORM on a separate
        # synchronous thread rather than disabling Django's async safety guard.
        def execute():
            try:
                return action()
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(execute).result(timeout=20)

    def setUp(self):
        call_command('seed_demo', verbosity=0)
        self.staff = User.objects.create_user('browser-staff', password='Browser-testing-823!')
        self.staff.groups.add(Group.objects.get(name='STAFF'))
        self.admin = User.objects.create_user('browser-admin', password='Browser-testing-823!', is_staff=True)
        self.admin.groups.add(Group.objects.get(name='ADMIN'))
        self.artifacts = Path('test-results/browser')
        self.artifacts.mkdir(parents=True, exist_ok=True)

    def login(self, page, username):
        page.goto(self.live_server_url + '/accounts/login/')
        page.locator('#id_username').fill(username)
        page.locator('#id_password').fill('Browser-testing-823!')
        page.get_by_role('button', name='Đăng nhập', exact=True).click()
        expect(page).to_have_url(self.live_server_url + '/menu/')

    def assert_images_loaded(self, page):
        # Native lazy images need viewport activation; navigation's load event
        # does not guarantee they have loaded. Keep a bounded wait per image.
        for image in page.locator('img').all():
            if image.is_visible():
                image.scroll_into_view_if_needed(timeout=10000)
            expect(image).to_have_js_property('complete', True, timeout=10000)
            self.assertGreater(image.evaluate('(i) => i.naturalWidth'), 0,
                f'Broken image: {image.get_attribute("src")}')
        self.assertTrue(page.evaluate(
            'Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)'),
            f'Images not loaded: {page.url}')
        page.evaluate('window.scrollTo(0, 0)')

    def test_lazy_image_wait_and_broken_image_detection_at_768(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 768, 'height': 1000})
            # Far below the browser's lazy-load threshold, with a cold URL:
            # reproduce the original assertion's failure without timing sleeps.
            page.set_content(f'<img loading="lazy" width="480" height="400" '
                f'style="margin-top:10000px" alt="Lazy image regression fixture" '
                f'src="{self.live_server_url}/static/catalog/drink.svg?lazy-regression=1">')
            self.assertFalse(page.evaluate(
                'Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)'))
            with page.expect_response(lambda response: '/static/catalog/drink.svg?lazy-regression=1' in response.url) as loaded:
                self.assert_images_loaded(page)
            self.assertEqual(loaded.value.status, 200)
            # A real HTTP failure still fails the same helper; no retry can
            # turn a missing image into a successful responsive check.
            page.set_content(f'<img alt="Broken image regression fixture" '
                f'src="{self.live_server_url}/static/catalog/missing-regression-image.svg">')
            with self.assertRaisesRegex(AssertionError, 'Broken image:'):
                self.assert_images_loaded(page)
            browser.close()

    def test_purchase_staff_review_and_responsive_pages(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'])
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='vi-VN')
            # External maps are optional; explicitly exercise the visible fallback offline.
            context.route('https://www.google.com/**', lambda route: route.abort())
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(self.live_server_url + '/accounts/register/')
            page.locator('#id_username').fill('browser-customer')
            page.locator('#id_password1').fill('Browser-testing-823!')
            page.locator('#id_password2').fill('Browser-testing-823!')
            page.get_by_role('button', name='Tạo tài khoản').click()
            self.login(page, 'browser-customer')
            page.goto(self.live_server_url + '/menu/?q=Cà+phê+sữa')
            page.locator('.product-card').get_by_role('link', name='Xem chi tiết', exact=True).click()
            page.locator('input[name="quantity"]').fill('2')
            page.get_by_role('button', name='Thêm vào giỏ').click()
            page.goto(self.live_server_url + '/checkout/')
            page.locator('#id_customer_name').fill('Khách browser DEMO')
            page.locator('#id_phone').fill('0900000000')
            page.locator('#id_payment_method').select_option('MOCK_ONLINE')
            page.locator('#id_accept_demo').check()
            page.get_by_role('button', name='Đặt đơn mô phỏng', exact=True).click()
            expect(page.get_by_role('heading', level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
            order = self.db(lambda: Order.objects.get(user__username='browser-customer'))
            self.assertEqual(order.total, 60000)
            self.assertTrue(self.db(lambda: bool(order.items.get().recipe_snapshot)))
            order_url = self.live_server_url + f'/account/orders/{order.public_code}/'
            page.get_by_role('button', name='Giả lập thất bại', exact=True).click()
            expect(page.locator('.order-summary .status-badge')).to_contain_text('Thanh toán mô phỏng thất bại')
            page.get_by_role('link', name='Mở mô phỏng thanh toán').click()
            page.get_by_role('button', name='Giả lập thành công', exact=True).click()
            staff_context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            staff_page = staff_context.new_page()
            self.login(staff_page, 'browser-staff')
            staff_page.goto(self.live_server_url + '/dashboard/orders/')
            process_staff_pickup(staff_page, order.public_code)
            self.assertEqual(self.db(lambda: LoyaltyLedger.objects.get(order=order).delta), 6)
            page.goto(order_url)
            expect(page.get_by_text('Đơn hàng đã hoàn thành', exact=False).first).to_be_visible()
            page.goto(self.live_server_url + '/products/ca-phe-sua-da/')
            page.locator('textarea[name="body"]').fill('Đánh giá DEMO từ hành trình trình duyệt.')
            page.get_by_role('button', name='Gửi đánh giá', exact=True).click()
            review = self.db(lambda: Review.objects.get(item__order=order))
            self.assertEqual(review.status, 'PENDING')
            admin_context = browser.new_context(viewport={'width': 1440, 'height': 1000})
            admin_page = admin_context.new_page()
            self.login(admin_page, 'browser-admin')
            admin_page.goto(self.live_server_url + f'/admin/support/review/{review.pk}/change/')
            admin_page.locator('#id_status').select_option('APPROVED')
            admin_page.locator('input[name="_save"]').click()
            self.assertEqual(self.db(lambda: Review.objects.get(pk=review.pk).status), 'APPROVED')
            page.reload()
            expect(page.get_by_text('Đánh giá DEMO từ hành trình trình duyệt.', exact=True)).to_be_visible()
            page.goto(self.live_server_url + '/contact/')
            page.locator('#id_name').fill('Khách DEMO')
            page.locator('#id_email').fill('browser@example.test')
            page.locator('#id_subject').fill('Browser smoke')
            page.locator('#id_body').fill('Kiểm thử liên hệ trong trình duyệt.')
            page.get_by_role('button', name='Gửi lời nhắn').click()
            self.assertTrue(self.db(lambda: Message.objects.filter(subject='Browser smoke').exists()))
            staff_page.goto(self.live_server_url + '/dashboard/orders/new-manual/')
            staff_page.locator('#id_channel').select_option('APP')
            staff_page.locator('#id_customer_name').fill('Khách APP DEMO')
            staff_page.locator('#id_external_reference').fill('BROWSER-APP-DEMO')
            variant_id = self.db(lambda: ProductVariant.objects.get(sku='CF02-STANDARD').pk)
            staff_page.locator('#id_lines-0-variant').select_option(str(variant_id))
            staff_page.locator('#id_lines-0-quantity').fill('2')
            staff_page.get_by_role('button', name='Tạo đơn', exact=True).click()
            expect(staff_page).to_have_url(self.live_server_url + '/dashboard/orders/')
            manual_total = self.db(lambda: Order.objects.get(external_reference='BROWSER-APP-DEMO').total)
            self.assertEqual(manual_total, 70000)
            paths = ['/', '/menu/', '/products/ca-phe-sua-da/', '/cart/', '/checkout/',
                '/contact/', '/feedback/', '/policies/returns/', '/account/loyalty/',
                '/account/profile/', '/account/addresses/', '/account/password/']
            for width in [375, 768, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                for index, path in enumerate(paths):
                    response = page.goto(self.live_server_url + path)
                    self.assertEqual(response.status, 200, path)
                    self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow: {width} {path}')
                    self.assert_images_loaded(page)
                    page.screenshot(path=str(self.artifacts / f'{width}-{index}.png'), full_page=True)
                if width == 375:
                    page.locator('.mobile-menu summary').click()
                    expect(page.locator('.mobile-menu').get_by_role('link', name='Thực đơn đồ uống')).to_be_visible()
                staff_page.set_viewport_size({'width': width, 'height': 1000})
                for index, path in enumerate(['/dashboard/orders/', '/dashboard/inventory/', '/dashboard/orders/new-manual/']):
                    self.assertEqual(staff_page.goto(self.live_server_url + path).status, 200)
                    self.assertTrue(staff_page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow: {width} {path}')
                    staff_page.screenshot(path=str(self.artifacts / f'{width}-staff-{index}.png'), full_page=True)
                admin_page.set_viewport_size({'width': width, 'height': 1000})
                self.assertEqual(admin_page.goto(self.live_server_url + '/dashboard/reports/').status, 200)
                self.assertTrue(admin_page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow: {width} reports')
                admin_page.screenshot(path=str(self.artifacts / f'{width}-reports.png'), full_page=True)
                print(f'PASS responsive: {width}px, {len(paths)} pages, screenshots saved')
            self.assertFalse(errors, errors)
            staff_context.close()
            admin_context.close()
            context.close()
            browser.close()

    def test_cart_update_remove_mock_refund_and_logout(self):
        buyer = self.customer()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 1440, 'height': 1000})
            self.login(page, buyer.username)
            self.add_drink(page)
            page.locator('input[name="quantity"]').fill('3')
            page.get_by_role('button', name='Cập nhật', exact=True).click()
            expect(page.locator('.cart-checkout-bar')).to_contain_text('90.000 đ')
            page.get_by_role('button', name='Xóa món khỏi giỏ', exact=True).click()
            expect(page.get_by_text('Giỏ hàng trống.', exact=False)).to_be_visible()
            self.add_drink(page)
            self.fill_checkout(page)
            page.get_by_role('button', name='Đặt đơn mô phỏng', exact=True).click()
            order = self.db(lambda: Order.objects.get(user=buyer))
            expect(page.get_by_role('heading', level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
            page.get_by_role('button', name='Giả lập thành công', exact=True).click()
            page.get_by_role('button', name='Yêu cầu hủy trước pha chế', exact=True).click()
            self.assertEqual(self.db(lambda: Order.objects.get(pk=order.pk).payment.status), 'REFUND_PENDING')
            admin_page = browser.new_page()
            self.login(admin_page, self.admin.username)
            admin_page.goto(self.live_server_url + '/dashboard/orders/?status=CANCELLED')
            admin_page.once('dialog',accept_staff_dialog)
            admin_page.get_by_role('button', name='Hoàn thanh toán mô phỏng', exact=True).click()
            self.assertEqual(self.db(lambda: Order.objects.get(pk=order.pk).payment.status), 'REFUNDED')
            page.reload()
            expect(page.locator('.order-summary .status-badge')).to_contain_text('Đã hoàn tiền mô phỏng')
            page.get_by_role('button', name='Đăng xuất', exact=True).click()
            page.goto(self.live_server_url + '/account/orders/')
            expect(page.locator('#id_username')).to_be_visible()
            self.assertIn('/accounts/login/', page.url)
            browser.close()

    def test_checkout_shortage_shows_error_and_keeps_cart(self):
        buyer = self.customer()
        cup = Ingredient.objects.get(sku='DEMO-CUP')
        adjust_stock(self.admin, cup.pk, -balance(cup), 'Hết ly trong browser test DEMO', uuid.uuid4())
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 375, 'height': 1000})
            self.login(page, buyer.username)
            self.add_drink(page, quantity=2)
            self.fill_checkout(page)
            page.get_by_role('button', name='Đặt đơn mô phỏng', exact=True).click()
            expect(page.get_by_text('Không đủ nguyên liệu', exact=False)).to_be_visible()
            self.assertFalse(self.db(lambda: Order.objects.filter(user=buyer).exists()))
            self.assertEqual(self.db(lambda: buyer.cart.items.get().quantity), 2)
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            page.screenshot(path=str(self.artifacts / '375-checkout-shortage.png'), full_page=True)
            browser.close()

    def test_pickup_and_partner_links_at_all_widths(self):
        buyer = self.customer()
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'])
            context = browser.new_context(locale='vi-VN')
            for url in ['https://food.grab.com/vn/vi/', 'https://shopeefood.vn/', 'https://food.be.com.vn/']:
                context.route(url, lambda route: route.fulfill(status=200, body='External platform test stub'))
            page = context.new_page()
            self.login(page, buyer.username)
            self.add_drink(page)
            for width in [375, 768, 1440]:
                page.set_viewport_size({'width':width,'height':1000})
                self.fill_checkout(page)
                expect(page.locator('#id_fulfillment option')).to_have_count(1)
                expect(page.locator('#id_payment_method option')).to_have_count(1)
                expect(page.locator('#id_address')).to_have_count(0)
                expect(page.locator('#id_scheduled_date')).to_have_count(1)
                expect(page.locator('#id_scheduled_hour option')).to_have_count(25)
                expect(page.locator('#id_scheduled_minute option')).to_have_count(61)
                expect(page.locator('input[type="datetime-local"]')).to_have_count(0)
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.screenshot(path=str(self.artifacts / f'{width}-pickup-checkout.png'),full_page=True)
                page.goto(self.live_server_url+'/delivery-partners/')
                expect(page.get_by_role('heading',level=1)).to_have_text('Đặt giao tận nơi qua đối tác')
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                links=page.locator('.partner-grid a')
                expect(links).to_have_count(3)
                for index in range(3):
                    link=links.nth(index)
                    href=link.get_attribute('href')
                    link.focus()
                    with context.expect_page() as popup:
                        page.keyboard.press('Enter')
                    popup.value.wait_for_load_state()
                    self.assertEqual(popup.value.url,href)
                    self.assertTrue(popup.value.evaluate('window.opener === null'))
                    popup.value.close()
                self.assertFalse(self.db(lambda: Order.objects.exists()))
                page.screenshot(path=str(self.artifacts / f'{width}-delivery-partners.png'),full_page=True)
            self.fill_checkout(page)
            page.get_by_role('button',name='Đặt đơn mô phỏng',exact=True).click()
            order=self.db(lambda:Order.objects.get(user=buyer))
            self.assertEqual(order.shipping,0)
            self.assertEqual(order.status,'PENDING_PAYMENT')
            expect(page.get_by_role('heading', level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
            page.get_by_role('button',name='Giả lập thành công',exact=True).click()
            staff_page=browser.new_page()
            self.login(staff_page,self.staff.username)
            staff_page.goto(self.live_server_url+'/dashboard/orders/')
            expect(staff_page.locator('article')).to_contain_text(str(order.public_code))
            process_staff_pickup(staff_page, order.public_code)
            self.assertEqual(self.db(lambda:Order.objects.get(pk=order.pk).status),'COMPLETED')
            self.assertEqual(self.db(lambda:Order.objects.get(pk=order.pk).payment.status),'PAID')
            browser.close()
