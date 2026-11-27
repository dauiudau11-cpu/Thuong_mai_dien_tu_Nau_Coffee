"""Refund and real standard-menu POS regressions on independent PostgreSQL QA."""
import json
import os
import uuid
from pathlib import Path
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import override_settings
from playwright.sync_api import sync_playwright, expect
from . import test_pickup_compatibility as compat
from commerce.models import Order, Payment, Cart
from commerce.services import add_item, place_order, simulate_payment
from catalog.models import ProductVariant


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class RefundPOSBrowserTests(StaticLiveServerTestCase):
    setUp=compat.CopiedDevelopmentBrowserTests.setUp
    db=compat.CopiedDevelopmentBrowserTests.db
    login=compat.CopiedDevelopmentBrowserTests.login
    browser=compat.CopiedDevelopmentBrowserTests.browser

    def tearDown(self):
        from tests.pickup_compatibility_fixture import history_state
        self.assertEqual(history_state(),self.original)
        super().tearDown()

    def evidence(self):
        p=Path(os.getenv('NAU_REFUND_POS_QA_ROOT','test-results/refund-pos'));p.mkdir(parents=True,exist_ok=True);return p

    def paid_order(self):
        cart,_=Cart.objects.get_or_create(user=self.buyer)
        add_item(cart,ProductVariant.objects.get(sku='CF02-360').pk,2)
        order=place_order(self.buyer,cart,dict(customer_name='Refund synthetic',phone='0900000000',
            fulfillment='PICKUP',payment_method='MOCK_ONLINE',idempotency_key=uuid.uuid4()))
        simulate_payment(self.buyer,order.payment.token,True)
        return Order.objects.get(pk=order.pk)

    def test_standard_pos_three_cards_post_saves_every_item_all_widths(self):
        trace=[]
        with sync_playwright() as p:
            browser=self.browser(p)
            for width in [375,768,1440]:
                context=browser.new_context(viewport={'width':width,'height':1000});page=context.new_page()
                errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
                self.login(page,self.staff.username);page.goto(self.live_server_url+'/dashboard/orders/new-manual/')
                page.locator('#id_customer_name').fill('POS three synthetic')
                for sku in ['CF03-360','TE02-700','TE01-700']:
                    variant=self.db(lambda sku=sku:ProductVariant.objects.get(sku=sku).pk)
                    page.locator(f'.pos-select[data-variant="{variant}"]').click()
                summary=page.locator('#manual-grand-total').inner_text()
                fields=page.locator('.manual-order-form').evaluate('(form)=>Array.from(new FormData(form).entries()).filter(([name])=>name!=="csrfmiddlewaretoken")')
                page.screenshot(path=str(self.evidence()/f'{width}-pos-three.png'),full_page=True)
                with page.expect_request(lambda request:request.method=='POST' and '/new-manual/' in request.url) as posted:
                    page.get_by_role('button',name='Tạo đơn',exact=True).click()
                expect(page).to_have_url(self.live_server_url+'/dashboard/orders/')
                order=self.db(lambda:Order.objects.get(customer_name='POS three synthetic',idempotency_key=dict(fields)['idempotency_key']))
                values=self.db(lambda:list(order.items.values('sku','quantity','line_total')))
                trace.append({'width':width,'fields':fields,'js_errors':errors,'http_method':posted.value.method,
                    'order':str(order.public_code),'summary':summary,'stored_items':values,'payment':self.db(lambda:Payment.objects.get(order=order).status),'total':order.total})
                (self.evidence()/'pos-http-proof.json').write_text(json.dumps(trace,indent=2,ensure_ascii=False))
                self.assertEqual(len(values),3)
                self.assertFalse(errors)
                self.assertEqual(order.total,105000)
                self.assertEqual(summary,'105.000 đ')
                context.close()
            browser.close()

    def test_refund_database_state_and_customer_has_clear_section(self):
        order=self.paid_order();trace=[]
        with sync_playwright() as p:
            browser=self.browser(p);customer=browser.new_page();self.login(customer,self.buyer.username)
            customer.goto(self.live_server_url+f'/account/orders/{order.public_code}/')
            customer.get_by_role('button',name='Yêu cầu hủy trước pha chế',exact=True).click()
            trace.append(self.db(lambda:{'stage':'customer_cancel','order':str(order.public_code),
                'order_status':Order.objects.get(pk=order.pk).status,'payment_status':Payment.objects.get(order=order).status,
                'refund_events':order.payment.events.filter(event_key='mock_refund').count()}))
            self.assertEqual(trace[-1]['payment_status'],'REFUND_PENDING');self.assertEqual(trace[-1]['refund_events'],0)
            admin=browser.new_page();self.login(admin,self.admin.username)
            admin.goto(self.live_server_url+'/dashboard/orders/?status=CANCELLED')
            response=admin.request.post(self.live_server_url+f'/dashboard/orders/{order.public_code}/refund/',
                form={'csrfmiddlewaretoken':admin.locator('input[name="csrfmiddlewaretoken"]').first.input_value()})
            trace.append(self.db(lambda:{'stage':'admin_post','http_status':response.status,
                'payment_status':Payment.objects.get(order=order).status,'refunded_at':str(Payment.objects.get(order=order).refunded_at),
                'refund_events':order.payment.events.filter(event_key='mock_refund').count(),
                'actor_is_admin':order.payment.events.get(event_key='mock_refund').actor_id==self.admin.pk}))
            (self.evidence()/'refund-http-proof.json').write_text(json.dumps(trace,indent=2))
            self.assertEqual(trace[-1]['payment_status'],'REFUNDED');self.assertTrue(trace[-1]['actor_is_admin'])
            customer.reload()
            expect(customer.get_by_role('heading',name='Hoàn tiền mô phỏng',exact=True)).to_be_visible()
            browser.close()

    def test_refund_pending_admin_confirmation_and_customer_receipt_all_widths(self):
        with sync_playwright() as p:
            browser=self.browser(p)
            for width in [375,768,1440]:
                order=self.db(self.paid_order)
                context=browser.new_context(viewport={'width':width,'height':1000});page=context.new_page()
                self.login(page,self.buyer.username);page.goto(self.live_server_url+f'/account/orders/{order.public_code}/')
                page.get_by_role('button',name='Yêu cầu hủy trước pha chế',exact=True).click()
                section=page.locator('.refund-status');expect(section).to_contain_text('Đang chờ Quản trị viên')
                expect(section).not_to_contain_text('Đã hoàn tiền mô phỏng')
                expect(section).to_contain_text('64.000 đ')
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                self.assertGreater(section.locator('dt').nth(2).bounding_box()['width'],100)
                self.assertLess(section.locator('dt').nth(2).bounding_box()['height'],60)
                page.screenshot(path=str(self.evidence()/f'{width}-customer-pending.png'),full_page=True)
                admin_context=browser.new_context(viewport={'width':width,'height':1000});admin=admin_context.new_page()
                self.login(admin,self.admin.username);admin.goto(self.live_server_url+'/dashboard/refunds/')
                row=admin.locator(f'[data-code="{order.public_code}"]');expect(row).to_be_visible()
                admin.screenshot(path=str(self.evidence()/f'{width}-admin-pending.png'),full_page=True)
                admin.once('dialog',lambda dialog:dialog.accept());row.get_by_role('button',name='Xác nhận hoàn tiền mô phỏng',exact=True).click()
                expect(admin).to_have_url(self.live_server_url+'/dashboard/refunds/')
                expect(admin.get_by_text('Đã xác nhận hoàn tiền mô phỏng. Không phát sinh tiền thật.',exact=True)).to_be_visible()
                self.assertEqual(self.db(lambda:Payment.objects.get(order=order).status),'REFUNDED')
                self.assertEqual(self.db(lambda:order.payment.events.filter(event_key='mock_refund',actor=self.admin).count()),1)
                page.reload();expect(section).to_contain_text('Đã hoàn tiền mô phỏng')
                page.screenshot(path=str(self.evidence()/f'{width}-customer-refunded.png'),full_page=True)
                admin.locator('[name="payment_status"]').select_option('REFUNDED');admin.get_by_role('button',name='Lọc',exact=True).click()
                expect(row.locator('button')).to_have_count(0);admin.screenshot(path=str(self.evidence()/f'{width}-admin-refunded.png'),full_page=True)
                self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
                self.assertFalse(admin.evaluate('document.documentElement.scrollWidth > innerWidth'))
                context.close();admin_context.close()
            browser.close()

    def test_pos_remove_change_quantity_and_invalid_row_keeps_other_items(self):
        with sync_playwright() as p:
            browser=self.browser(p);page=browser.new_page(viewport={'width':375,'height':1000})
            errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
            self.login(page,self.staff.username);page.goto(self.live_server_url+'/dashboard/orders/new-manual/')
            page.locator('#id_customer_name').fill('POS invalid synthetic')
            ids={sku:self.db(lambda sku=sku:ProductVariant.objects.get(sku=sku).pk) for sku in ['CF03-360','TE02-700','TE01-700']}
            for sku in ids:page.locator(f'.pos-select[data-variant="{ids[sku]}"]').click()
            page.locator('.manual-line').nth(1).get_by_role('button',name='Bỏ dòng món này').click()
            expect(page.locator('#id_lines-TOTAL_FORMS')).to_have_value('2')
            page.locator('#id_lines-0-quantity').fill('2')
            expect(page.locator('#manual-grand-total')).to_have_text('104.000 đ')
            page.locator('#id_lines-1-variant').select_option(str(ids['TE02-700']))
            expect(page.locator('#manual-grand-total')).to_have_text('100.000 đ')
            # Submit invalid quantity via fetch to exercise server validation, not native HTML blocking.
            page.locator('#id_lines-1-quantity').fill('0')
            html=page.locator('.manual-order-form').evaluate("async form => (await fetch(form.action || location.href,{method:'POST',body:new FormData(form)})).text()")
            self.assertIn('POS invalid synthetic',html);self.assertIn('errorlist',html)
            self.assertFalse(self.db(lambda:Order.objects.filter(customer_name='POS invalid synthetic').exists()))
            self.assertFalse(errors);self.assertFalse(page.evaluate('document.documentElement.scrollWidth > innerWidth'))
            browser.close()
