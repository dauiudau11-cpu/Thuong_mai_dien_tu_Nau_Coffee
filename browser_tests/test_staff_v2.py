"""Real Chromium Staff V2, polling, drawer and payment on an independent QA cluster."""
import os
import uuid
from pathlib import Path
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from playwright.sync_api import sync_playwright, expect
from commerce.models import Cart, Order, Payment, StockMovement
from commerce.services import add_item, place_order, simulate_payment
from commerce.staff import staff_command, version
from catalog.models import ProductVariant
from . import test_pickup_compatibility as compat


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class StaffV2BrowserTests(StaticLiveServerTestCase):
    setUp=compat.CopiedDevelopmentBrowserTests.setUp
    def tearDown(self):
        from tests.pickup_compatibility_fixture import history_state
        self.assertEqual(history_state(),self.original)
        super().tearDown()

    db=compat.CopiedDevelopmentBrowserTests.db
    login=compat.CopiedDevelopmentBrowserTests.login
    browser=compat.CopiedDevelopmentBrowserTests.browser

    def order(self,counter=False):
        if counter:
            from commerce.operations import manual_order
            order=manual_order(self.staff,dict(channel='COUNTER',customer_name='V2 POS DEMO',phone='0900000000',idempotency_key=uuid.uuid4()),
                [{'variant':ProductVariant.objects.get(sku='CF02-360'),'quantity':2,'options':[]}])
            return Order.objects.select_related('payment').get(pk=order.pk)
        cart,_=Cart.objects.get_or_create(user=self.buyer)
        add_item(cart,ProductVariant.objects.get(sku='CF02-360').pk,2)
        order=place_order(self.buyer,cart,dict(customer_name='V2 browser DEMO',phone='0900000000',
            fulfillment='PICKUP',payment_method='MOCK_ONLINE',idempotency_key=uuid.uuid4()))
        simulate_payment(self.buyer,order.payment.token,True)
        return Order.objects.select_related('payment').get(pk=order.pk)

    def test_three_buttons_completed_drawer_and_pos_payment_at_all_widths(self):
        artifact=Path(os.getenv('NAU_STAFF_QA_ROOT','test-results/staff-v2'));artifact.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as p:
            browser=self.browser(p)
            for width in [375,768,1440]:
                order=self.db(self.order)
                context=browser.new_context(viewport={'width':width,'height':1000});page=context.new_page()
                self.login(page,self.staff.username);page.goto(self.live_server_url+'/dashboard/kitchen/')
                page.on('dialog',lambda dialog:dialog.accept())
                card=page.locator(f'[data-code="{order.public_code}"]')
                expect(card.locator('[data-command="cash"]')).to_have_count(0)
                expect(card).to_contain_text('Đã thanh toán mô phỏng')
                url=page.url;navigations=[];page.on('framenavigated',lambda frame:navigations.append(frame.url))
                for label,state in [('Bắt đầu pha chế','PREPARING'),('Pha xong','PICKUP_WAITING'),('Đã giao khách','COMPLETED')]:
                    card.get_by_role('button',name=label,exact=True).click()
                    expect(card).to_have_attribute('data-status',state)
                    self.assertEqual(page.url,url)
                self.assertFalse(navigations)
                card.locator('[data-open]').click();expect(page.locator('#staff-drawer')).to_be_visible()
                expect(page.locator('#staff-detail')).to_contain_text('Bàn giao hoàn tất')
                expect(page.locator('#staff-detail [data-command]')).to_have_count(0)
                page.screenshot(path=str(artifact/f'{width}-completed-drawer.png'),full_page=True)
                page.get_by_role('button',name='Đóng chi tiết').click()
                counter=self.db(lambda:self.order(counter=True));page.reload()
                card=page.locator(f'[data-code="{counter.public_code}"]')
                card.get_by_role('button',name='Ghi nhận đã thu tiền mô phỏng').click()
                expect(card).to_contain_text('Đã thanh toán mô phỏng')
                expect(card.locator('[data-command="cash"]')).to_have_count(0)
                self.assertEqual(self.db(lambda:Payment.objects.get(order=counter).status),'PAID')
                self.assertEqual(self.db(lambda:counter.payment.events.filter(event_key='cash_demo').count()),1)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                page.screenshot(path=str(artifact/f'{width}-kanban.png'),full_page=True)
                context.close()
            browser.close()

    def test_polling_pauses_hidden_and_does_not_replace_pending_action(self):
        order=self.db(self.order)
        with sync_playwright() as p:
            browser=self.browser(p);page=browser.new_page()
            page.clock.install();self.login(page,self.staff.username)
            page.goto(self.live_server_url+'/dashboard/kitchen/')
            feeds=[];page.on('request',lambda request: feeds.append(request.url) if request.url.endswith('/kitchen/data/') else None)
            page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>true})")
            page.clock.run_for(24050);self.assertFalse(feeds)
            page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,get:()=>false})")
            page.evaluate("""() => {
              const original=window.fetch;
              window.fetch=async (...args)=>{
                if(String(args[0]).endsWith('/action/')) await new Promise(resolve=>window.releaseStaffRequest=resolve);
                return original(...args);
              };
            }""")
            card=page.locator(f'[data-code="{order.public_code}"]')
            card.get_by_role('button',name='Bắt đầu pha chế',exact=True).click()
            expect(card.locator('[data-command="start"]')).to_be_disabled()
            page.clock.run_for(12050)
            self.assertFalse(feeds);expect(card).to_have_attribute('data-status','CONFIRMED')
            page.evaluate('window.releaseStaffRequest()')
            expect(card).to_have_attribute('data-status','PREPARING')
            self.assertEqual(self.db(lambda:order.history.filter(to_state='PREPARING').count()),1)
            browser.close()

    def test_polling_new_orders_keeps_drawer_draft_and_syncs_other_staff(self):
        order=self.db(self.order)
        with sync_playwright() as p:
            browser=self.browser(p);page=browser.new_page(viewport={'width':768,'height':1000})
            page.clock.install()
            self.login(page,self.staff.username);page.goto(self.live_server_url+'/dashboard/kitchen/')
            card=page.locator(f'[data-code="{order.public_code}"]');card.locator('[data-open]').click()
            draft=page.locator('#staff-draft');draft.fill('Ghi chú đang nhập, chưa lưu')
            new=self.db(self.order)
            def other_staff():
                current=Order.objects.select_related('payment').get(pk=order.pk)
                staff_command(self.admin,current.public_code,'start',version(current))
            self.db(other_staff)
            page.clock.run_for(12050)
            expect(page.locator(f'[data-code="{new.public_code}"]')).to_be_visible()
            expect(card).to_have_attribute('data-status','PREPARING')
            expect(page.locator('#staff-drawer')).to_be_visible()
            expect(draft).to_have_value('Ghi chú đang nhập, chưa lưu')
            expect(page.locator('#staff-detail')).to_contain_text('Đang pha chế')
            page.get_by_role('button',name='Đóng chi tiết').click()
            # A stale request from an outdated tab is rejected and cannot consume again.
            before=self.db(lambda:StockMovement.objects.filter(order=order).count())
            response=page.request.post(self.live_server_url+f'/dashboard/kitchen/{order.public_code}/action/',
                form={'action':'start','version':version(order),'csrfmiddlewaretoken':page.locator('#staff-csrf input').input_value()})
            self.assertEqual(response.status,409)
            self.assertEqual(self.db(lambda:StockMovement.objects.filter(order=order).count()),before)
            browser.close()
