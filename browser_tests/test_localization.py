"""Vietnamese admin labels must remain usable at phone/tablet/desktop widths."""
import json
import os
import re
from pathlib import Path
from django.conf import settings
from django.contrib import admin
from django.test import override_settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright
from catalog.localization import MODEL_NAMES
from .test_journey import BrowserJourneyTests


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class LocalizationBrowserTests(StaticLiveServerTestCase):
    setUp = BrowserJourneyTests.setUp
    db = BrowserJourneyTests.db

    def test_admin_registered_screens_labels_filters_and_responsive(self):
        def prepare():
            self.admin.is_superuser=True
            self.admin.save(update_fields=['is_superuser'])
            self.client.force_login(self.admin)
            return self.client.cookies[settings.SESSION_COOKIE_NAME].value
        cookie=self.db(prepare)
        root=Path(os.getenv('NAU_QA_ROOT','test-results/localization'))/'localized-admin';root.mkdir(parents=True,exist_ok=True)
        paths=['/admin/']
        for model in admin.site._registry:
            opts=model._meta
            if opts.app_label in MODEL_NAMES:
                paths.append(f'/admin/{opts.app_label}/{opts.model_name}/')
        paths += ['/admin/commerce/voucher/add/','/admin/catalog/product/add/',
                  '/admin/catalog/channelprice/add/','/admin/commerce/ingredient/add/',
                  '/admin/auth/user/add/','/admin/auth/group/add/',
                  '/admin/commerce/voucher/?q=NO-MATCH&kind__exact=FIXED']
        rows=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
            context=browser.new_context(locale='vi-VN');context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':cookie,'url':self.live_server_url}])
            page=context.new_page()
            for width in [375,768,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                for i,path in enumerate(paths):
                    response=page.goto(self.live_server_url+path,wait_until='networkidle')
                    if path=='/admin/support/consentevent/':
                        self.assertEqual(response.status,403,path)
                        rows.append({'page':path,'width':width,'status':403,'access':'policy feature OFF'})
                        continue
                    self.assertEqual(response.status,200,path)
                    page.evaluate('async()=>await document.fonts.ready')
                    body=page.locator('body').inner_text()
                    unwanted=re.findall(r'\b(?:Code|Kind|Amount|Cap|Min subtotal|Max uses|Per user limit|Starts at|Ends at|Is active|Allow sale stacking|Product variants|Channel prices|Stock movements|Dashboard|Inventory|PENDING_PAYMENT|CONFIRMED|PREPARING|REFUND_PENDING)\b',body)
                    self.assertFalse(unwanted,(path,unwanted))
                    overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
                    self.assertFalse(overflow,(path,width))
                    fonts=page.locator('body').evaluate('e=>getComputedStyle(e).fontFamily');self.assertIn('Be Vietnam Pro',fonts)
                    name=f'{width}-{i:02d}.png';page.screenshot(path=str(root/name),full_page=True)
                    rows.append({'page':path,'width':width,'status':response.status,'overflow':overflow,'unwanted_labels':unwanted,'body_font':fonts,'screenshot':name})
            browser.close()
        (root/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
