"""WIP screenshots use only the guarded test database, never laptop orders/users."""
import json
import os
from pathlib import Path
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright, expect
from commerce.models import Cart
from commerce.services import add_item
from catalog.models import ProductVariant
from .typography_audit import audit_page, install_windows_georgia
from . import test_journey


class WIPVisualTests(StaticLiveServerTestCase):
    setUp = test_journey.BrowserJourneyTests.setUp
    customer = test_journey.BrowserJourneyTests.customer

    def assert_images_loaded(self, page):
        for image in page.locator('img:visible').all():
            image.scroll_into_view_if_needed(timeout=10000)
            expect(image).to_have_js_property('complete', True, timeout=10000)
            self.assertGreater(image.evaluate('(image) => image.naturalWidth'), 0)
        page.evaluate('window.scrollTo(0, 0)')
        # Lazy-image activation may scroll the category rail horizontally.
        page.locator('.premium-category-rail').evaluate_all('(rails) => rails.forEach(rail => rail.scrollLeft = 0)')

    def test_customer_and_operations_screens(self):
        buyer = self.customer()
        cart = Cart.objects.create(user=buyer)
        add_item(cart, ProductVariant.objects.get(sku='CF02-STANDARD').pk, 2)
        phase = os.getenv('NAU_QA_PHASE', 'after')
        directory = Path(os.getenv('NAU_QA_ROOT', 'docs/qa/2026-10-28')) / phase
        directory.mkdir(parents=True, exist_ok=True)
        rows = []
        links = []
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'])
            for role, user, pages in [
                ('customer', buyer, [('home', '/'), ('menu', '/menu/'), ('product', '/products/ca-phe-sua-da/'),
                    ('cart', '/cart/'), ('checkout', '/checkout/'), ('partners', '/delivery-partners/'), ('login', '/accounts/login/'),
                    ('account', '/account/'), ('profile', '/account/profile/'), ('addresses', '/account/addresses/'),
                    ('orders', '/account/orders/'), ('loyalty', '/account/loyalty/'),
                    ('contact', '/contact/'), ('policy', '/policies/shipping/')]),
                ('staff', self.staff, [('dashboard', '/dashboard/'), ('queue', '/dashboard/orders/'),
                    ('manual', '/dashboard/orders/new-manual/'), ('inventory', '/dashboard/inventory/'), ('kitchen', '/dashboard/kitchen/')]),
                ('admin', self.admin, [('reports', '/dashboard/reports/'), ('catalog-admin', '/admin/catalog/product/')] +
                    [(section, '/dashboard/manage/' + section + '/') for section in ['products', 'categories', 'promotions', 'customers', 'staff']] +
                    [('config-' + section, '/dashboard/settings/' + section + '/') for section in ['store', 'appearance', 'payment', 'delivery', 'notifications', 'security']]),
            ]:
                # Playwright owns an event loop, so session setup uses the helper thread.
                def session():
                    self.client.force_login(user)
                    return self.client.cookies[settings.SESSION_COOKIE_NAME].value
                cookie = test_journey.BrowserJourneyTests.db(self, session)
                context = browser.new_context(locale='vi-VN')
                install_windows_georgia(context)
                context.add_cookies([{'name': settings.SESSION_COOKIE_NAME, 'value': cookie, 'url': self.live_server_url}])
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                for width in [375, 768, 1440]:
                    page.set_viewport_size({'width': width, 'height': 1000})
                    for name, path in pages:
                        response = page.goto(self.live_server_url + path)
                        self.assertEqual(response.status, 200, f'{role}/{name}')
                        page.evaluate('async()=>{await window.nauInstalledGeorgia;await document.fonts.ready;}')
                        self.assert_images_loaded(page)
                        fonts = audit_page(page, strict=phase == 'after')
                        if name == 'home':
                            if phase == 'after':
                                self.assertIn('Noto Serif', page.locator('.premium-hero-script').evaluate('e=>getComputedStyle(e).fontFamily'))
                            hero = page.locator('.premium-hero')
                            for label, href in [('Đặt trước, nhận tại quán', '/menu/'), ('Muốn giao tận nơi?', '/delivery-partners/')]:
                                link = hero.get_by_role('link', name=label)
                                expect(link).to_be_visible()
                                expect(link).to_have_attribute('href', href)
                                bounds, frame = link.bounding_box(), hero.bounding_box()
                                self.assertLessEqual(bounds['y'] + bounds['height'], frame['y'] + frame['height'])
                        if name == 'partners':
                            expect(page.locator('.partner-grid a[target="_blank"]')).to_have_count(3)
                        if phase == 'after' and name in ('home', 'menu', 'product', 'cart', 'checkout', 'login'):
                            footer = page.locator('.premium-footer')
                            expect(footer.locator('.footer-tagline')).to_have_text(
                                'Một chút Nâu mỗi ngày, cho những khoảnh khắc đẹp hơn.')
                            self.assertNotIn('Website đồ án', footer.inner_text())
                            self.assertNotIn('DEMO', footer.inner_text())
                            self.assertTrue(footer.locator('.footer-tagline').evaluate('''element => {
                                const style = getComputedStyle(element);
                                return element.scrollWidth <= element.clientWidth &&
                                    style.wordBreak === 'normal' && style.letterSpacing === 'normal' &&
                                    parseFloat(style.fontSize) >= 14;
                            }'''))
                        overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth')
                        screenshot = f'{width}-{role}-{name}.png'
                        page.screenshot(path=str(directory / screenshot), full_page=True)
                        rows.append({'role': role, 'page': path, 'width': width, 'http': response.status,
                            'overflow': overflow, 'screenshot': screenshot, 'typography': fonts})
                        if phase == 'after':
                            self.assertFalse(overflow, f'{name}: {width}px overflow')
                self.assertFalse(errors)
                if phase == 'after':
                    seen = set()
                    for _, path in pages:
                        page.goto(self.live_server_url + path)
                        targets = page.locator('a[href]').evaluate_all('(items)=>items.map(a=>a.href)')
                        for target in targets:
                            if not target.startswith(self.live_server_url + '/') or target in seen:
                                continue
                            seen.add(target)
                            response = context.request.get(target)
                            self.assertEqual(response.status, 200, f'Broken {role} link: {target}')
                            links.append({'role': role, 'path': target.removeprefix(self.live_server_url), 'status': response.status})
                context.close()
            browser.close()
        (directory / 'manifest.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
        if phase == 'after':
            (directory / 'links.json').write_text(json.dumps(links, ensure_ascii=False, indent=2))
