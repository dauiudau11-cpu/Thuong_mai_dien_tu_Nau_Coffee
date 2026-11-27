"""Full browser journeys against the anonymized real catalog, 50 BOM lines and legacy orders."""
import os
from datetime import time, timedelta
from pathlib import Path
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from django.utils import timezone
from playwright.sync_api import sync_playwright, expect
from catalog.models import ProductVariant
from commerce.models import Ingredient, Order, PaymentEvent, StockMovement, StoreSettings
from commerce.operations import balance
from tests.pickup_compatibility_fixture import load_compatibility_fixture, create_role_user, history_state
from . import test_journey as journey


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class CopiedDevelopmentBrowserTests(StaticLiveServerTestCase):
    db=journey.BrowserJourneyTests.db
    login=journey.BrowserJourneyTests.login
    fill_checkout=journey.BrowserJourneyTests.fill_checkout

    def setUp(self):
        load_compatibility_fixture()
        self.buyer=create_role_user('compat-browser-buyer','CUSTOMER')
        self.staff=create_role_user('compat-browser-staff','STAFF')
        self.admin=create_role_user('compat-browser-admin','ADMIN')
        self.original=history_state()
        self.artifacts=Path(os.getenv('NAU_COMPAT_QA_ROOT','docs/qa/2026-11-10-pickup-review/e2e'))
        self.artifacts.mkdir(parents=True,exist_ok=True)

    def tearDown(self):
        self.assertEqual(history_state(),self.original)
        super().tearDown()

    def browser(self,playwright):
        return playwright.chromium.launch(executable_path=os.getenv('CHROMIUM_PATH','/usr/bin/chromium'),
            headless=True,args=['--no-sandbox'])

    def add(self,page,sku):
        slug=self.db(lambda:ProductVariant.objects.get(sku=sku).product.slug)
        page.goto(self.live_server_url+'/products/'+slug+'/')
        page.locator('input[name="quantity"]').fill('2')
        page.get_by_role('button',name='Thêm vào giỏ',exact=True).click()

    def csrf(self,page):
        return page.locator('input[name="csrfmiddlewaretoken"]').first.input_value()

    def confirm(self,page):
        self.fill_checkout(page)
        page.get_by_role('button',name='Đặt đơn mô phỏng',exact=True).click()
        expect(page.get_by_role('heading',level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
        return self.db(lambda:Order.objects.select_related('payment').filter(user=self.buyer).latest('pk'))

    def pay(self,page,outcome):
        if '/payments/mock/' not in page.url:
            page.get_by_role('link',name='Mở mô phỏng thanh toán',exact=True).click()
        expect(page.get_by_role('heading',level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
        page.get_by_role('button',name='Giả lập thành công' if outcome=='success' else 'Giả lập thất bại',exact=True).click()

    def test_guest_merge_tampering_retry_staff_bom_and_pickup_completion(self):
        with sync_playwright() as playwright:
            browser=self.browser(playwright)
            customer=browser.new_context(locale='vi-VN',viewport={'width':1440,'height':1000})
            page=customer.new_page()
            self.add(page,'CF02-360')
            page.goto(self.live_server_url+'/checkout/')
            expect(page.locator('#id_username')).to_be_visible()
            self.login(page,self.buyer.username)
            self.fill_checkout(page)
            initial_movements=self.db(lambda:StockMovement.objects.count())
            initial_balances=self.db(lambda:{i.pk:balance(i) for i in Ingredient.objects.all()})
            payload={
                'customer_name':'Compatibility buyer','phone':'0900000000','fulfillment':'DELIVERY',
                'payment_method':'MOCK_ONLINE','accept_demo':'on','action':'place',
                'idempotency_key':page.locator('#id_idempotency_key').input_value(),
                'csrfmiddlewaretoken':self.csrf(page),
            }
            response=customer.request.post(self.live_server_url+'/checkout/',form=payload)
            self.assertEqual(response.status,200)
            self.assertEqual(self.db(lambda:Order.objects.count()),5)
            for width in [375,768,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                expect(page.locator('#id_address')).to_have_count(0)
                expect(page.locator('#id_scheduled_date')).to_have_count(1)
                expect(page.locator('#id_scheduled_hour option')).to_have_count(25)
                expect(page.locator('#id_scheduled_minute option')).to_have_count(61)
                expect(page.locator('input[type="datetime-local"]')).to_have_count(0)
                expect(page.locator('#id_payment_method option')).to_have_count(1)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(self.artifacts/f'{width}-copied-checkout.png'),full_page=True)
            page.get_by_role('button',name='Đặt đơn mô phỏng',exact=True).click()
            expect(page.get_by_role('heading',level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
            order=self.db(lambda:Order.objects.select_related('payment').get(user=self.buyer))
            self.assertEqual(order.total,64000)
            self.assertEqual(order.status,'PENDING_PAYMENT')
            self.assertEqual(order.shipping,0)
            for width in [375,768,1440]:
                page.set_viewport_size({'width':width,'height':1000})
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth>innerWidth'))
                page.screenshot(path=str(self.artifacts/f'{width}-direct-payment.png'),full_page=True)
            payload['fulfillment']='PICKUP'
            customer.request.post(self.live_server_url+'/checkout/',form=payload)
            self.assertEqual(self.db(lambda:Order.objects.count()),6)
            self.pay(page,'failure')
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=order.pk).payment.status),'FAILED')
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=order.pk).status),'PENDING_PAYMENT')
            self.pay(page,'success')
            customer.request.post(self.live_server_url+f'/payments/mock/{order.payment.token}/',
                form={'outcome':'success','csrfmiddlewaretoken':self.csrf(page)})
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=order.pk).status),'CONFIRMED')
            self.assertEqual(self.db(lambda:StockMovement.objects.count()),initial_movements)
            staff=browser.new_context(locale='vi-VN')
            staff_page=staff.new_page();self.login(staff_page,self.staff.username)
            staff_page.goto(self.live_server_url+'/dashboard/kitchen/')
            card=staff_page.locator('.kitchen-card').filter(has_text=str(order.public_code)[:8])
            expect(card).to_have_count(1)
            old_version=card.get_attribute('data-version')
            journey.process_staff_pickup(staff_page,order.public_code,[('Bắt đầu pha chế','PREPARING')])
            replay=staff_page.request.post(self.live_server_url+f'/dashboard/kitchen/{order.public_code}/action/',
                form={'action':'start','version':old_version,'csrfmiddlewaretoken':staff_page.locator('#staff-csrf input').input_value()})
            self.assertEqual(replay.status,409)
            expected=self.db(lambda:{l.ingredient_id:l.quantity*2 for l in ProductVariant.objects.get(sku='CF02-360').recipe.all()})
            self.assertEqual(self.db(lambda:{i.pk:balance(i) for i in Ingredient.objects.all()}),
                {pk:value-expected.get(pk,0) for pk,value in initial_balances.items()})
            self.assertEqual(self.db(lambda:StockMovement.objects.filter(order_id=order.pk).count()),6)
            page.reload();expect(page.get_by_role('button',name='Yêu cầu hủy trước pha chế')).to_have_count(0)
            customer.request.post(self.live_server_url+f'/account/orders/{order.public_code}/cancel/',
                form={'csrfmiddlewaretoken':self.csrf(page)})
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=order.pk).status),'PREPARING')
            journey.process_staff_pickup(staff_page,order.public_code,[('Pha xong','PICKUP_WAITING'),('Đã giao khách','COMPLETED')])
            completed=self.db(lambda:Order.objects.select_related('payment').get(pk=order.pk))
            self.assertEqual(completed.status,'COMPLETED')
            self.assertEqual(completed.payment.status,'PAID')
            self.assertEqual(self.db(lambda:PaymentEvent.objects.filter(payment__order_id=order.pk,event_key='mock_success').count()),1)
            page.reload();expect(page.locator('.status-badge',has_text='Đơn hàng đã hoàn thành')).to_be_visible()
            page.screenshot(path=str(self.artifacts/'1440-copied-completed.png'),full_page=True)
            browser.close()

    def test_checkout_uses_24_hour_controls_and_stores_selected_times(self):
        self.db(lambda: StoreSettings.objects.filter(name='DEMO').update(
            opens_at=time(0, 0), closes_at=time(23, 59), preorder_days=3, slot_capacity=20))
        selected_date = timezone.localdate() + timedelta(days=1)
        cases = [(375, '09', '30'), (768, '14', '30'), (1440, '23', '00')]
        with sync_playwright() as playwright:
            browser = self.browser(playwright)
            context = browser.new_context(locale='vi-VN', viewport={'width': 375, 'height': 1000})
            page = context.new_page()
            self.login(page, self.buyer.username)
            for width, hour, minute in cases:
                page.set_viewport_size({'width': width, 'height': 1000})
                self.add(page, 'CF02-360')
                self.fill_checkout(page)
                page.locator('#id_scheduled_date').fill(selected_date.isoformat())
                page.locator('#id_scheduled_hour').select_option(hour)
                page.locator('#id_scheduled_minute').select_option(minute)
                expect(page.locator('input[type="datetime-local"]')).to_have_count(0)
                expect(page.locator('#id_scheduled_hour')).to_have_value(hour)
                expect(page.locator('#id_scheduled_minute')).to_have_value(minute)
                self.assertNotIn('SA/CH', page.locator('.pickup-time-field').inner_text())
                page.screenshot(path=str(self.artifacts/f'{width}-checkout-24h-{hour}{minute}.png'), full_page=True)
                page.get_by_role('button', name='Đặt đơn mô phỏng', exact=True).click()
                expect(page.get_by_role('heading', level=1)).to_have_text('THANH TOÁN MÔ PHỎNG')
                stored = self.db(lambda: Order.objects.filter(user=self.buyer).latest('pk').scheduled_for)
                local = timezone.localtime(stored)
                self.assertEqual((local.date(), local.hour, local.minute), (selected_date, int(hour), int(minute)))
            browser.close()

    def test_unpaid_cancel_paid_cancel_staff_denial_admin_refund_and_replay(self):
        with sync_playwright() as playwright:
            browser=self.browser(playwright)
            customer=browser.new_context(locale='vi-VN')
            page=customer.new_page();self.login(page,self.buyer.username)
            count=self.db(lambda:StockMovement.objects.count())
            self.add(page,'CF01-360');unpaid=self.confirm(page)
            page.get_by_role('link',name='← Trở về đơn hàng',exact=True).click()
            page.get_by_role('button',name='Yêu cầu hủy trước pha chế',exact=True).click()
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=unpaid.pk).payment.status),'PENDING')
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=unpaid.pk).status),'CANCELLED')
            self.add(page,'CF03-360');paid=self.confirm(page);self.pay(page,'success')
            page.get_by_role('button',name='Yêu cầu hủy trước pha chế',exact=True).click()
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=paid.pk).payment.status),'REFUND_PENDING')
            customer.request.post(self.live_server_url+f'/payments/mock/{paid.payment.token}/',
                form={'outcome':'success','csrfmiddlewaretoken':self.csrf(page)})
            staff=browser.new_context();staff_page=staff.new_page();self.login(staff_page,self.staff.username)
            denied=staff.request.post(self.live_server_url+f'/dashboard/orders/{paid.public_code}/refund/',
                form={'csrfmiddlewaretoken':self.csrf(staff_page)})
            self.assertEqual(denied.status,403)
            admin=browser.new_context();admin_page=admin.new_page();self.login(admin_page,self.admin.username)
            admin_page.goto(self.live_server_url+'/dashboard/orders/?status=CANCELLED')
            card=admin_page.locator('.queue-order').filter(has_text=str(paid.public_code))
            token=self.csrf(admin_page)
            admin_page.once('dialog',lambda dialog:dialog.accept())
            card.get_by_role('button',name='Hoàn thanh toán mô phỏng',exact=True).click()
            admin.request.post(self.live_server_url+f'/dashboard/orders/{paid.public_code}/refund/',
                form={'csrfmiddlewaretoken':token})
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=paid.pk).payment.status),'REFUNDED')
            self.assertEqual(self.db(lambda:Order.objects.select_related('payment').get(pk=paid.pk).status),'CANCELLED')
            self.assertEqual(self.db(lambda:PaymentEvent.objects.filter(payment__order_id=paid.pk,event_key='mock_refund').count()),1)
            self.assertEqual(self.db(lambda:StockMovement.objects.count()),count)
            page.reload();expect(page.locator('.order-summary .status-badge').get_by_text('Đã hoàn tiền mô phỏng',exact=True)).to_be_visible()
            page.screenshot(path=str(self.artifacts/'1440-copied-refunded.png'),full_page=True)
            browser.close()
