"""Browser acceptance for staged menu; test-only supply is explicit."""
import io
import json
import os
import uuid
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from playwright.sync_api import sync_playwright, expect
from catalog.models import ProductVariant
from commerce.models import Cart, CartItem, Order
from tests import test_standard_menu as standard_menu_tests
from .test_journey import BrowserJourneyTests


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class StandardMenuBrowserTests(StaticLiveServerTestCase):
    setUp = BrowserJourneyTests.setUp
    customer = BrowserJourneyTests.customer
    db = BrowserJourneyTests.db
    supply = standard_menu_tests.StandardMenuTests.supply
    assert_images_loaded = BrowserJourneyTests.assert_images_loaded

    def test_paused_catalog_stale_cart_and_ready_pickup_journey(self):
        buyer=self.customer()
        cart=Cart.objects.create(user=buyer)
        old=CartItem.objects.create(cart=cart,variant=ProductVariant.objects.get(sku='CF04-M'),quantity=1,config_key='test')
        before=(old.variant_id,old.quantity)
        call_command('prepare_standard_menu',apply=True,cutover=True,stdout=io.StringIO())
        self.client.force_login(buyer)
        cookie=self.client.cookies[settings.SESSION_COOKIE_NAME].value
        root=Path(os.getenv('NAU_STANDARD_QA_ROOT', 'docs/qa/2026-11-10-pickup/standard-menu'))
        root.mkdir(parents=True,exist_ok=True)
        manifest=[]
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),headless=True,args=['--no-sandbox'])
            context=browser.new_context(locale='vi-VN')
            context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':cookie,'url':self.live_server_url}])
            page=context.new_page()
            for width in [375,768,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                for name,path in [('menu','/menu/'),('product','/products/ca-phe-sua-da/'),('cart','/cart/'),('checkout','/checkout/')]:
                    response=page.goto(self.live_server_url+path)
                    self.assertEqual(response.status,200)
                    if name=='product':
                        expect(page.get_by_text('Tạm chưa nhận đặt món.',exact=False)).to_be_visible()
                        expect(page.get_by_role('button',name='Thêm vào giỏ',exact=True)).to_have_count(0)
                    if name=='cart':expect(page.get_by_text('Lựa chọn cũ đã ngừng bán;',exact=False).last).to_be_visible()
                    self.assert_images_loaded(page)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    screenshot=f'{width}-paused-{name}.png'
                    page.screenshot(path=str(root/screenshot),full_page=True)
                    manifest.append({'width':width,'page':name,'state':'paused','http':200,'overflow':False,'screenshot':screenshot})
            self.assertEqual(self.db(lambda:CartItem.objects.filter(pk=old.pk).values_list('variant_id','quantity').get()),before)
            def ready():
                self.supply()
                call_command('prepare_standard_menu',apply=True,activate=True,stdout=io.StringIO())
            self.db(ready)
            page.goto(self.live_server_url+'/cart/')
            page.get_by_role('button',name='Xóa món khỏi giỏ',exact=True).click()
            page.goto(self.live_server_url+'/products/ca-phe-sua-da/')
            page.locator('input[name="quantity"]').fill('3')
            page.get_by_role('button',name='Thêm vào giỏ',exact=True).click()
            expect(page.locator('.cart-checkout-bar')).to_contain_text('96.000')
            def approved_products():
                return [(v.product.slug, v.pk, v.prices.get(channel='WEB').current_price)
                    for v in ProductVariant.objects.filter(size='FIXED').select_related('product').order_by('sku')]
            approved=self.db(approved_products)
            self.assertEqual(len(approved),8)
            page.goto(self.live_server_url+'/checkout/')
            expect(page.locator('#id_fulfillment option')).to_have_count(1)
            self.assertEqual(page.locator('#id_fulfillment').input_value(),'PICKUP')
            expect(page.locator('#id_address')).to_have_count(0)
            for width in [375,768,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                for name,path in [('home','/'),('menu','/menu/'),('product','/products/ca-phe-sua-da/'),('cart','/cart/'),('checkout','/checkout/')]:
                    self.assertEqual(page.goto(self.live_server_url+path).status,200)
                    self.assert_images_loaded(page)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    screenshot=f'{width}-ready-{name}.png'
                    page.screenshot(path=str(root/screenshot),full_page=True)
                    manifest.append({'width':width,'page':name,'state':'ready','http':200,'overflow':False,'screenshot':screenshot})
                    if name in ('home','menu'):
                        prices=page.locator('.home-product-price, .product-card-bottom strong').all_text_contents()
                        self.assertTrue(prices)
                        self.assertFalse(any(text.strip().startswith('Từ ') for text in prices))
                for slug,variant_id,web_price in approved:
                    self.assertEqual(page.goto(self.live_server_url+'/products/'+slug+'/').status,200)
                    expect(page.locator('.product-media img')).to_be_visible()
                    expect(page.locator('.product-media figcaption')).to_have_count(0)
                    expect(page.locator('.variant-price')).to_have_text(f'{web_price:,}'.replace(',', '.')+' đ')
                    expect(page.locator('.purchase-form input[name="variant"]')).to_have_value(str(variant_id))
                    self.assert_images_loaded(page)
                    self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                    manifest.append({'width':width,'page':slug,'state':'approved-detail','http':200,
                        'overflow':False,'image_loaded':True,'web_price':web_price,'variant_id':variant_id})
            page.goto(self.live_server_url+'/checkout/')
            page.locator('#id_customer_name').fill('Test customer')
            page.locator('#id_phone').fill('0900000000')
            page.locator('#id_accept_demo').check()
            page.get_by_role('button',name='Đặt đơn mô phỏng',exact=True).click()
            self.assertIn('/payments/mock/',page.url)
            expect(page.get_by_role('heading',level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
            def order_values():
                order=Order.objects.get(user=buyer)
                return order.total,order.shipping,order.fulfillment,list(order.items.values_list('sku','unit_price'))
            self.assertEqual(self.db(order_values),(96000,0,'PICKUP',[('CF02-360',32000)]))
            context.close()
            for role,user,paths in [('staff',self.staff,[('pos','/dashboard/orders/new-manual/')]),
                    ('admin',self.admin,[('products','/dashboard/manage/products/'),('cost','/admin/catalog/standardcost/')])]:
                def login_cookie():
                    self.client.force_login(user)
                    return self.client.cookies[settings.SESSION_COOKIE_NAME].value
                cookie=self.db(login_cookie)
                context=browser.new_context(locale='vi-VN')
                context.add_cookies([{'name':settings.SESSION_COOKIE_NAME,'value':cookie,'url':self.live_server_url}])
                page=context.new_page()
                for width in [375,768,1440]:
                    page.set_viewport_size({'width':width,'height':1000})
                    for name,path in paths:
                        self.assertEqual(page.goto(self.live_server_url+path).status,200)
                        self.assert_images_loaded(page)
                        self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                        screenshot=f'{width}-ready-{role}-{name}.png'
                        page.screenshot(path=str(root/screenshot),full_page=True)
                        manifest.append({'width':width,'page':name,'role':role,'state':'ready','http':200,'overflow':False,'screenshot':screenshot})
                if role=='staff':
                    page.locator('#id_channel').select_option('APP')
                    variant_id=self.db(lambda:ProductVariant.objects.get(sku='CF01-360').pk)
                    page.locator(f'.pos-select[data-variant="{variant_id}"]').click()
                    page.locator('#id_customer_name').fill('Test POS')
                    page.locator('#id_external_reference').fill(str(uuid.uuid4()))
                    page.get_by_role('button',name='Tạo đơn',exact=True).click()
                    expect(page).to_have_url(self.live_server_url+'/dashboard/orders/')
                    self.assertEqual(self.db(lambda:Order.objects.get(channel='APP').total),37000)
                context.close()

            browser.close()
        (root/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
