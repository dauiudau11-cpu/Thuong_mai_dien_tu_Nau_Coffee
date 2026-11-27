"""Self-hosted fonts must render every Vietnamese tone/glyph offline without fallback."""
import json
import os
import unicodedata
from pathlib import Path
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from playwright.sync_api import sync_playwright
from .typography_audit import install_windows_georgia
from . import test_journey


class VietnameseFontTests(StaticLiveServerTestCase):
    db=test_journey.BrowserJourneyTests.db
    def test_vietnamese_nfc_nfd_inventory_all_weights_offline(self):
        phrases=['niềm vui','Hồ sơ','lần gần','Nâu lắng nghe','lời nhắn','Tóm tắt giỏ hàng','Tóm tắt đơn']
        inventory='ĂăÂâĐđÊêÔôƠơƯư '+''.join(chr(i) for i in range(0x1ea0,0x1efa))
        root=Path(os.getenv('NAU_QA_ROOT','test-results/typography'));root.mkdir(parents=True,exist_ok=True)
        results=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
            context=browser.new_context();windows_georgia=install_windows_georgia(context)
            context.route('https://**/*',lambda route:route.abort())
            page=context.new_page();page.goto(self.live_server_url+'/healthz/')
            page.set_content(f'''<meta charset="utf-8"><link rel="stylesheet" href="{self.live_server_url}/static/catalog/fonts.css"><style>body{{margin:24px}}p{{font-size:24px;line-height:1.5;overflow-wrap:anywhere}}</style><main></main>''')
            for width in [375,768,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                for family in ['Noto Serif','Be Vietnam Pro']:
                    for weight in [400,500,600,700]:
                        value=' · '.join(phrases)+' · '+inventory+' · '+unicodedata.normalize('NFD',' '.join(phrases)+inventory)
                        page.evaluate('''({family,weight,value})=>{const main=document.querySelector('main');main.replaceChildren();const p=document.createElement('p');p.id='font-probe';p.style.fontFamily=`"${family}"`;p.style.fontWeight=weight;p.textContent=value;main.append(p);}''',{'family':family,'weight':weight,'value':value})
                        page.evaluate('async()=>await document.fonts.ready')
                        self.assertTrue(page.evaluate('(family)=>document.fonts.check(`400 24px "${family}"`)',family))
                        session=context.new_cdp_session(page);session.send('DOM.enable');session.send('CSS.enable')
                        node=session.send('DOM.querySelector',{'nodeId':session.send('DOM.getDocument')['root']['nodeId'],'selector':'#font-probe'})['nodeId']
                        fonts=session.send('CSS.getPlatformFontsForNode',{'nodeId':node})['fonts'];session.detach()
                        self.assertTrue(fonts)
                        self.assertTrue(all(f['isCustomFont'] and f['postScriptName'].split('-')[0]==family.replace(' ','') for f in fonts),fonts)
                        self.assertEqual(page.locator('#font-probe').text_content(),value)
                        self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                        results.append({'family':family,'weight':weight,'width':width,'glyph_fonts':fonts,'nfc_and_nfd_preserved':True})
                    page.screenshot(path=str(root/f'{width}-{family.replace(" ","-")}-glyphs.png'),full_page=True)
            # An active promotional banner exercises the reported niềm-vui phrase.
            def promotion():
                from commerce.models import Voucher
                from django.utils import timezone
                from datetime import timedelta
                Voucher.objects.create(code='FONT-QA',kind='FIXED',amount=1000,
                    starts_at=timezone.now()-timedelta(days=1),ends_at=timezone.now()+timedelta(days=1))
            self.db(promotion)
            promo=[]
            for width in [375,768,1440]:
                page.set_viewport_size({'width':width,'height':1000});page.goto(self.live_server_url+'/')
                page.evaluate('async()=>{await window.nauInstalledGeorgia;await document.fonts.ready;}')
                title=page.locator('.premium-voucher-hero h2');text=title.text_content()
                self.assertIn('niềm vui',text);self.assertEqual(unicodedata.normalize('NFC',text),text)
                title.evaluate("el=>el.style.setProperty('font-family','Georgia,serif')")
                for phase in ['before','after']:
                    if phase=='after':title.evaluate("el=>el.style.removeProperty('font-family')")
                    page.evaluate('async()=>await document.fonts.ready')
                    session=context.new_cdp_session(page);session.send('DOM.enable');session.send('CSS.enable')
                    node=session.send('DOM.querySelector',{'nodeId':session.send('DOM.getDocument')['root']['nodeId'],'selector':'.premium-voucher-hero h2'})['nodeId']
                    fonts=session.send('CSS.getPlatformFontsForNode',{'nodeId':node})['fonts'];session.detach()
                    if phase=='before' and windows_georgia:self.assertGreater(len({f['familyName'] for f in fonts}),1)
                    if phase=='after':self.assertTrue(all(f['isCustomFont'] and f['postScriptName'].startswith('NotoSerif-') for f in fonts),fonts)
                    directory=root/phase;directory.mkdir(exist_ok=True)
                    page.locator('.premium-voucher-hero').screenshot(path=str(directory/f'{width}-promo-banner.png'))
                    self.assertEqual(title.text_content(),text)
                    promo.append({'phase':phase,'width':width,'text':text,'fonts':fonts,'installed_windows_georgia':windows_georgia})
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
            (root/'promo-font-audit.json').write_text(json.dumps(promo,ensure_ascii=False,indent=2))
            browser.close()
        (root/'vietnamese-glyph-audit.json').write_text(json.dumps(results,indent=2))
