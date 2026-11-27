"""Locked Staff commands and HTTP contract; exclusively the guarded QA PostgreSQL."""
import io
import uuid
from unittest.mock import patch
from django.contrib.auth.models import User, Group
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase, Client, TransactionTestCase
from commerce.models import Cart, Order, Payment, PaymentEvent, StockMovement, Ingredient
from commerce.services import add_item, place_order, simulate_payment
from commerce.staff import staff_command, version
from catalog.models import ProductVariant


def setup(owner):
    call_command('seed_demo', stdout=io.StringIO())
    for attr, role in [('buyer','CUSTOMER'),('staff','STAFF'),('admin','ADMIN')]:
        user=User.objects.create_user('v2-'+attr)
        user.groups.add(Group.objects.get(name=role));setattr(owner,attr,user)
    owner.variant=ProductVariant.objects.get(sku='CF02-STANDARD')


def make_order(owner, counter=False):
    if counter:
        from commerce.operations import manual_order
        order=manual_order(owner.staff,dict(channel='COUNTER',customer_name='Staff V2 POS synthetic',phone='0900000000',idempotency_key=uuid.uuid4()),
            [{'variant':owner.variant,'quantity':2,'options':[]}])
        return Order.objects.select_related('payment').get(pk=order.pk)
    cart,_=Cart.objects.get_or_create(user=owner.buyer)
    add_item(cart,owner.variant.pk,2)
    order=place_order(owner.buyer,cart,dict(customer_name='Staff V2 synthetic',phone='0900000000',
        fulfillment='PICKUP',payment_method='MOCK_ONLINE',idempotency_key=uuid.uuid4()))
    simulate_payment(owner.buyer,order.payment.token,True)
    return Order.objects.select_related('payment').get(pk=order.pk)


class StaffV2Tests(TestCase):
    @classmethod
    def setUpTestData(cls):setup(cls)

    def setUp(self):
        self.order=make_order(self);self.client.force_login(self.staff)

    def post(self,action,**extra):
        self.order=Order.objects.select_related('payment').get(pk=self.order.pk)
        return self.client.post(f'/dashboard/kitchen/{self.order.public_code}/action/',
            {'action':action,'version':version(self.order),**extra})

    def test_three_buttons_complete_with_exact_history_and_stock_once(self):
        for action,state in [('start','PREPARING'),('finish','PICKUP_WAITING'),('handover','COMPLETED')]:
            response=self.post(action,confirmed='yes');self.assertEqual(response.status_code,200)
            self.assertEqual(response.json()['status'],state)
            self.assertNotIn('Location',response)
        self.order.refresh_from_db()
        self.assertEqual(list(self.order.history.order_by('pk').values_list('to_state',flat=True)),
            ['PENDING_PAYMENT','CONFIRMED','PREPARING','READY','PICKUP_WAITING','COMPLETED'])
        self.assertFalse(self.order.history.filter(from_state='READY',to_state='READY').exists())
        self.assertTrue(StockMovement.objects.filter(order=self.order).exists())
        self.assertEqual(self.post('handover',confirmed='yes').status_code,400)

    def test_finish_chain_rolls_back_if_second_transition_fails(self):
        self.post('start');self.order.refresh_from_db();before=self.order.history.count()
        from commerce.services import transition_order
        def fail(actor,code,state,reason):
            if state=='PICKUP_WAITING':raise ValidationError('Injected second-step failure')
            return transition_order(actor,code,state,reason)
        with patch('commerce.staff.transition_order',side_effect=fail):self.assertEqual(self.post('finish').status_code,400)
        self.order.refresh_from_db();self.assertEqual(self.order.status,'PREPARING');self.assertEqual(self.order.history.count(),before)

    def test_duplicate_stale_request_rejected_without_stock_replay(self):
        payload={'action':'start','version':version(self.order)};url=f'/dashboard/kitchen/{self.order.public_code}/action/'
        self.assertEqual(self.client.post(url,payload).status_code,200)
        before=list(StockMovement.objects.filter(order=self.order).values())
        self.assertEqual(self.client.post(url,payload).status_code,409)
        self.assertEqual(before,list(StockMovement.objects.filter(order=self.order).values()))

    def test_paid_web_has_no_cash_action_and_cannot_capture_again(self):
        page=self.client.get('/dashboard/kitchen/');self.assertNotContains(page,'data-command="cash"')
        before=self.order.payment.events.count();response=self.post('cash');self.assertEqual(response.status_code,400)
        self.assertIn('MOCK_ONLINE',response.json()['error']);self.assertEqual(self.order.payment.events.count(),before)

    def test_counter_capture_updates_database_and_event_once(self):
        self.order=make_order(self,counter=True)
        self.assertContains(self.client.get('/dashboard/kitchen/'),'data-command="cash"')
        self.assertEqual(self.post('cash').json()['payment_status'],'PAID')
        self.assertEqual(Payment.objects.get(order=self.order).status,'PAID')
        self.assertEqual(self.post('cash').status_code,400)
        self.assertEqual(PaymentEvent.objects.filter(payment__order=self.order,event_key='cash_demo').count(),1)
        self.assertEqual(Payment.objects.filter(order=self.order).count(),1)

    def test_reproduce_legacy_cash_endpoint_web_rejects_counter_saves(self):
        # Same endpoint/services as before Staff V2: WEB is already paid and is not a cash method.
        response=self.client.post(f'/dashboard/orders/{self.order.public_code}/cash/')
        self.assertEqual(response.status_code,302);self.assertEqual(Payment.objects.get(order=self.order).status,'PAID')
        import json
        print('STAFF_V2_REPRO '+json.dumps({'order':str(self.order.public_code),'channel':'WEB','method':'MOCK_ONLINE','payment_before':'PAID','order_before':'CONFIRMED','http_method':'POST','endpoint':f'/dashboard/orders/{self.order.public_code}/cash/','http_status':response.status_code,'validation':'cash method rejected; no write','payment_after':Payment.objects.get(order=self.order).status,'cash_events':self.order.payment.events.filter(event_key='cash_demo').count()}))
        counter=make_order(self,counter=True)
        response=self.client.post(f'/dashboard/orders/{counter.public_code}/cash/')
        self.assertEqual(response.status_code,302);self.assertEqual(Payment.objects.get(order=counter).status,'PAID')
        print('STAFF_V2_REPRO '+json.dumps({'order':str(counter.public_code),'channel':'COUNTER','method':'PAY_AT_PICKUP','payment_before':'UNPAID','order_before':'CONFIRMED','http_method':'POST','endpoint':f'/dashboard/orders/{counter.public_code}/cash/','http_status':response.status_code,'validation':'allowed','payment_after':Payment.objects.get(order=counter).status,'cash_events':counter.payment.events.filter(event_key='cash_demo').count()}))

    def test_unpaid_mock_cannot_start_or_mark_cash(self):
        Payment.objects.filter(order=self.order).update(status='FAILED')
        self.assertEqual(self.post('start').status_code,400);self.assertEqual(self.post('cash').status_code,400)
        self.order.refresh_from_db();self.assertEqual(self.order.status,'CONFIRMED')
        self.assertFalse(StockMovement.objects.filter(order=self.order).exists())
        self.assertContains(self.client.get('/dashboard/kitchen/'),'Cần kiểm tra')

    def test_insufficient_stock_does_not_mutate_order_payment_or_history(self):
        StockMovement.objects.all().delete() # Isolated fixture supply only.
        before=self.order.history.count()
        response=self.post('start');self.assertEqual(response.status_code,400)
        self.assertIn('Không đủ',response.json()['error'])
        self.order.refresh_from_db();self.assertEqual(self.order.status,'CONFIRMED')
        self.assertEqual(self.order.history.count(),before);self.assertEqual(self.order.payment.status,'PAID')

    def test_missing_legacy_bom_blocks_without_mapping_or_snapshot_write(self):
        self.order.items.update(recipe_snapshot=None);self.variant.recipe.all().delete()
        before=self.order.history.count();response=self.post('start')
        self.assertEqual(response.status_code,400);self.assertIn('Đơn cũ thiếu',response.json()['error'])
        self.assertIsNone(self.order.items.get().recipe_snapshot);self.assertEqual(self.order.history.count(),before)

    def test_handover_requires_confirmation(self):
        self.post('start');self.post('finish');self.assertEqual(self.post('handover').status_code,400)
        self.order.refresh_from_db();self.assertEqual(self.order.status,'PICKUP_WAITING')

    def test_completed_detail_readable_without_mutating(self):
        self.post('start');self.post('finish');self.post('handover',confirmed='yes')
        before=list(Order.objects.filter(pk=self.order.pk).values())
        response=self.client.get(f'/dashboard/kitchen/{self.order.public_code}/')
        self.assertEqual(response.status_code,200);self.assertIn('Bàn giao hoàn tất',response.json()['html'])
        self.assertNotIn('data-command',response.json()['html']);self.assertEqual(before,list(Order.objects.filter(pk=self.order.pk).values()))

    def test_permission_csrf_and_methods(self):
        url=f'/dashboard/kitchen/{self.order.public_code}/action/'
        self.assertEqual(self.client.get(url).status_code,405)
        secure=Client(enforce_csrf_checks=True);secure.force_login(self.staff)
        self.assertEqual(secure.post(url,{'action':'start','version':version(self.order)}).status_code,403)
        self.client.force_login(self.buyer)
        for path in ['/dashboard/kitchen/data/',f'/dashboard/kitchen/{self.order.public_code}/']:
            self.assertEqual(self.client.get(path).status_code,403)
        self.assertEqual(self.post('start').status_code,403)
        self.client.force_login(self.staff)
        self.assertNotContains(self.client.get('/dashboard/orders/'),'class="queue-form"')
        self.client.force_login(self.admin)
        self.assertContains(self.client.get('/dashboard/orders/'),'Quản trị viên · xử lý ngoại lệ')
        self.assertEqual(self.post('start').status_code,200)

    def test_forged_backwards_and_unknown_actions_rejected(self):
        for action in ['COMPLETED','CONFIRMED','refund','PREPARING','']:
            self.assertEqual(self.post(action).status_code,400)
        self.assertFalse(StockMovement.objects.filter(order=self.order).exists())

    def test_history_same_state_entries_separated_and_new_rejections_not_history(self):
        from commerce.models import OrderStatusHistory
        OrderStatusHistory.objects.create(order=self.order,from_state='READY',to_state='READY',actor=self.staff,reason='Từ chối thao tác: historical')
        before=self.order.history.count()
        with self.assertLogs('nau.staff',level='WARNING'):
            self.client.post(f'/dashboard/orders/{self.order.public_code}/transition/',{'status':'COMPLETED'})
        self.assertEqual(self.order.history.count(),before)
        html=self.client.get(f'/dashboard/kitchen/{self.order.public_code}/').json()['html']
        self.assertIn('không phải chuyển trạng thái',html)

    def test_ready_to_ready_request_is_rejected_without_new_history(self):
        self.post('start')
        from commerce.services import transition_order
        transition_order(self.staff,self.order.public_code,'READY')
        before=self.order.history.count()
        self.client.force_login(self.admin)
        with self.assertLogs('nau.staff',level='WARNING'):
            response=self.client.post(f'/dashboard/orders/{self.order.public_code}/transition/',{'status':'READY'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.order.history.count(),before)
        self.assertEqual(self.post('finish').status_code,400)
        self.assertFalse(self.order.history.filter(from_state='READY',to_state='READY').exists())

    def test_board_polling_and_legacy_remain_accessible(self):
        response=self.client.get('/dashboard/kitchen/data/');self.assertEqual(response.status_code,200)
        self.assertIn(str(self.order.public_code),response.json()['html'])
        Order.objects.filter(pk=self.order.pk).update(fulfillment='DELIVERY',channel='APP')
        self.assertEqual(self.post('start').status_code,400)
        self.assertContains(self.client.get('/dashboard/kitchen/'),'Luồng riêng')
        self.assertEqual(self.client.get('/dashboard/orders/?fulfillment=DELIVERY').status_code,200)


class StaffV2RaceTests(TransactionTestCase):
    def setUp(self):setup(self);self.order=make_order(self)

    def test_two_staff_same_version_only_one_consumes(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        barrier=Barrier(2);v=version(self.order)
        second=User.objects.create_user('v2-second');second.groups.add(Group.objects.get(name='STAFF'))
        def run(actor):
            try:
                barrier.wait(timeout=10)
                try:staff_command(actor,self.order.public_code,'start',v);return 'ok'
                except ValidationError:return 'stale'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(run,[self.staff,second]))
        self.assertCountEqual(result,['ok','stale'])
        self.assertEqual(self.order.history.filter(to_state='PREPARING').count(),1)
        self.assertEqual(StockMovement.objects.filter(order=self.order,ingredient__sku='DEMO-CUP').count(),1)
