import os

from django.test import SimpleTestCase
from playwright.sync_api import sync_playwright


class AdminNavigationStateBrowserTests(SimpleTestCase):
    def test_sidebar_page_tabs_history_and_error_priority(self):
        script = os.path.join(os.path.dirname(__file__), '..', 'static', 'catalog', 'admin-navigation.js')

        def html(path):
            active = path.rstrip('/').rsplit('/', 1)[-1] or 'a'
            rows = ''.join(f'<a href="/admin/item-{index}/">Mục {index}</a>' for index in range(18))
            rows += f'<a id="to-b" href="/admin/b/" {'aria-current="page"' if active == 'b' else ''}>B</a>'
            rows += ''.join(f'<a href="/admin/item-{index}/">Mục {index}</a>' for index in range(18, 30))
            error = '<p class="errornote">Vui lòng sửa lỗi.</p>' if active == 'error' else ''
            return f'''<!doctype html><html><head><style>#nav-sidebar{{position:fixed;top:0;left:0}}#nav-sidebar a{{display:block;height:24px}}.reference-tabs{{position:fixed;top:0;right:0}}</style></head><body>
              <button class="nau-mobile-navigation" aria-expanded="false">Menu</button>
              <nav id="nav-sidebar" style="height:160px;overflow-y:auto">{rows}</nav>
              <nav class="reference-tabs"><a id="to-c" href="/admin/c/">Cấu hình C</a></nav>
              {error}<main style="height:3000px">Trang {active}</main>
            </body></html>'''

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                executable_path=os.getenv('CHROMIUM_PATH', '/usr/bin/chromium'),
                headless=True, args=['--no-sandbox'],
            )
            for width in (1440, 768, 375):
                context = browser.new_context(viewport={'width': width, 'height': 600})
                page = context.new_page()
                page.add_init_script(path=script)
                page.route('http://admin.test/**', lambda route: route.fulfill(
                    status=200, content_type='text/html', body=html(route.request.url.split('admin.test', 1)[1].split('?', 1)[0])
                ))
                page.goto('http://admin.test/admin/a/')
                page.evaluate("document.querySelector('#nav-sidebar').scrollTop=420; scrollTo(0,600)")
                page.wait_for_timeout(100)
                self.assertEqual(page.evaluate("sessionStorage.getItem('nau.admin.navigation.sidebar')"), '420')
                self.assertEqual(page.evaluate("sessionStorage.getItem('nau.admin.navigation.page:/admin/a/')"), '600')
                page.evaluate("sessionStorage.setItem('nau.admin.navigation.page:/admin/b/', '600')")
                page.goto('http://admin.test/admin/b/')
                page.wait_for_function("scrollY===600 && document.querySelector('#nav-sidebar').scrollTop===420")
                self.assertEqual(page.locator('#to-b').get_attribute('aria-current'), 'page')

                page.evaluate("document.querySelector('#nav-sidebar').scrollTop=560; scrollTo(0,900)")
                page.wait_for_timeout(100)
                page.evaluate("sessionStorage.setItem('nau.admin.navigation.page:/admin/c/', '900')")
                page.goto('http://admin.test/admin/c/')
                page.wait_for_function("scrollY===900 && document.querySelector('#nav-sidebar').scrollTop===560")
                page.go_back()
                page.wait_for_function("location.pathname==='/admin/b/' && scrollY===900")
                page.go_forward()
                page.wait_for_function("location.pathname==='/admin/c/' && scrollY===900")

                page.evaluate("sessionStorage.setItem('nau.admin.navigation.page:/admin/error/', '800')")
                page.goto('http://admin.test/admin/error/')
                self.assertEqual(page.evaluate('scrollY'), 0)
                context.close()
            browser.close()
