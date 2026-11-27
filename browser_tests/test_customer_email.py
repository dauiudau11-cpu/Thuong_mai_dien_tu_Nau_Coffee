"""Offline email rendering only, not live Gmail delivery or Gmail-app acceptance."""
import json
import os
from pathlib import Path
from django.test import SimpleTestCase
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright


class CustomerEmailResponsiveTests(SimpleTestCase):
    def test_html_at_mobile_tablet_desktop_no_external_resources(self):
        output=Path(os.environ.get('NAU_GMAIL_QA_ROOT','docs/qa/2026-11-12-gmail-smtp'))/'email-browser'
        output.mkdir(parents=True,exist_ok=True);rows=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ['CHROMIUM_PATH'],args=['--no-sandbox'])
            page=browser.new_page(locale='vi-VN');requests=[]
            page.route('**/*',lambda route:(requests.append('blocked'),route.abort()))
            for width in (375,768,1440):
                page.set_viewport_size({'width':width,'height':1000})
                for invitation in (False,True):
                    html=render_to_string('emails/customer_activation.html',dict(username='email-fixture',
                        activation_url='https://coffee.example.invalid/accounts/activate/#token='+'fixture-not-a-real-token'*12,
                        invitation=invitation,expiry_hours=24))
                    page.set_content(html)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                    self.assertIn('24 giờ',page.locator('body').inner_text())
                    self.assertEqual(page.locator('a').count(),2)
                    page.screenshot(path=str(output/f'{width}-{"invitation" if invitation else "activation"}.png'),
                        full_page=True,mask=[page.locator('a').last])
                    rows.append({'width':width,'invitation':invitation,'overflow':False,'token_text_masked':True})
            self.assertEqual(requests,[]);browser.close()
        (output/'responsive.json').write_text(json.dumps(rows,indent=2)+'\n')
