"""Refund audit/state and full POS formset regression using anonymized QA-only data."""
from collections import defaultdict
from decimal import Decimal
import uuid
from django.test import TestCase,TransactionTestCase,override_settings
from django.core.exceptions import ValidationError,PermissionDenied
from catalog.models import ProductVariant
from commerce.models import Order,Payment,PaymentEvent,Cart,Ingredient,StockMovement,RecipeLine
from commerce.services import add_item,place_order,simulate_payment,transition_order,refund_mock
from commerce.staff import staff_command,version
from commerce.operations import balance
from .pickup_compatibility_fixture import load_compatibility_fixture,create_role_user,history_state


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class RefundPOSTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        load_compatibility_fixture()
        cls.buyer=create_role_user('refund-pos-buyer','CUSTOMER');cls.staff=create_role_user('refund-pos-staff','STAFF');cls.admin=create_role_user('refund-pos-admin','ADMIN')

    def setUp(self):self.original=history_state()
    def tearDown(self):self.assertEqual(history_state(),self.original)

    def paid(self,paid=True):
        cart,_=Cart.objects.get_or_create(user=self.buyer);add_item(cart,ProductVariant.objects.get(sku='CF02-360').pk,2)
        order=place_order(self.buyer,cart,dict(customer_name='Refund QA',phone='0900000000',fulfillment='PICKUP',payment_method='MOCK_ONLINE',idempotency_key=uuid.uuid4()))
        if paid:simulate_payment(self.buyer,order.payment.token,True)
        return Order.objects.select_related('payment').get(pk=order.pk)

    def payload(self,skus,qtys=None):
        self.client.force_login(self.staff)
        token=self.client.get('/dashboard/orders/new-manual/').context['form'].initial['idempotency_key']
        data={'channel':'COUNTER','customer_name':'Multi QA','idempotency_key':token,'lines-TOTAL_FORMS':str(len(skus)),'lines-INITIAL_FORMS':'0','lines-MAX_NUM_FORMS':'10','lines-MIN_NUM_FORMS':'1'}
        for i,sku in enumerate(skus):data.update({f'lines-{i}-variant':ProductVariant.objects.get(sku=sku).pk,f'lines-{i}-quantity':(qtys or [1]*len(skus))[i]})
        return data

    def test_refund_explicit_pending_admin_confirmation_and_audit(self):
        o=self.paid();original=(o.subtotal,o.discount,o.total);stock=list(StockMovement.objects.values())
        self.client.force_login(self.buyer);self.client.post(f'/account/orders/{o.public_code}/cancel/')
        o.refresh_from_db();self.assertEqual(o.payment.status,'REFUND_PENDING')
        event=o.payment.events.get(event_key='refund_requested');self.assertEqual(event.actor_id,self.buyer.pk)
        self.assertFalse(o.payment.events.filter(event_key='mock_refund').exists())
        response=self.client.get(f'/account/orders/{o.public_code}/');self.assertContains(response,'Đang chờ Quản trị viên');self.assertNotContains(response,'Đã hoàn tiền mô phỏng')
        for user in [self.buyer,self.staff]:
            self.client.force_login(user);self.assertEqual(self.client.get('/dashboard/refunds/').status_code,403)
            self.assertEqual(self.client.post(f'/dashboard/orders/{o.public_code}/refund/').status_code,403)
        self.client.force_login(self.admin);response=self.client.get('/dashboard/refunds/');self.assertContains(response,str(o.public_code))
        response=self.client.post(f'/dashboard/orders/{o.public_code}/refund/',{'return_to':'refunds'},follow=True)
        self.assertContains(response,'Đã xác nhận hoàn tiền mô phỏng')
        o.refresh_from_db();self.assertEqual(o.payment.status,'REFUNDED');self.assertIsNotNone(o.payment.refunded_at)
        self.assertEqual(o.payment.events.get(event_key='mock_refund').actor_id,self.admin.pk)
        response=self.client.post(f'/dashboard/orders/{o.public_code}/refund/',{'return_to':'refunds'},follow=True)
        self.assertContains(response,'không tạo giao dịch hoàn lần hai');self.assertEqual(o.payment.events.filter(event_key='mock_refund').count(),1)
        self.client.force_login(self.buyer);self.assertContains(self.client.get(f'/account/orders/{o.public_code}/'),'Đã hoàn tiền mô phỏng')
        self.assertEqual((o.subtotal,o.discount,o.total),original);self.assertEqual(list(StockMovement.objects.values()),stock)

    def test_ineligible_and_unpaid_refunds_rejected(self):
        paid=self.paid();unpaid=self.paid(False)
        transition_order(self.buyer,unpaid.public_code,'CANCELLED')
        for o in [paid,unpaid]:
            with self.assertRaises(ValidationError):refund_mock(self.admin,o.public_code,strict=True)
        self.assertFalse(PaymentEvent.objects.filter(payment__order__in=[paid,unpaid],event_key='mock_refund').exists())

    def test_legacy_refunded_without_event_is_not_fabricated(self):
        o=self.paid();transition_order(self.buyer,o.public_code,'CANCELLED')
        Payment.objects.filter(order=o).update(status='REFUNDED');o.payment.events.filter(event_key='refund_requested').delete()
        self.client.force_login(self.buyer);before=list(o.payment.events.values())
        self.assertContains(self.client.get(f'/account/orders/{o.public_code}/'),'chưa có ghi nhận xác nhận')
        self.assertEqual(before,list(o.payment.events.values()))

    def test_pos_one_two_three_and_duplicates_quantities(self):
        for skus,qtys in [(['CF03-360'],[1]),(['CF03-360','TE02-700'],[1,2]),(['CF03-360','TE02-700','TE01-700'],[2,3,4]),(['CF03-360','CF03-360'],[2,3])]:
            with self.subTest(skus=skus):
                data=self.payload(skus,qtys);before=Order.objects.count();response=self.client.post('/dashboard/orders/new-manual/',data)
                self.assertEqual(response.status_code,302);self.assertEqual(Order.objects.count(),before+1)
                o=Order.objects.get(idempotency_key=data['idempotency_key']);self.assertEqual(o.items.count(),len(skus))
                self.assertEqual(list(o.items.order_by('pk').values_list('quantity',flat=True)),qtys)
                self.assertEqual(o.total,sum(item.line_total for item in o.items.all()));self.assertEqual(o.discount,0)
                self.assertEqual(o.payment.amount,o.total);self.assertEqual(o.payment.status,'UNPAID')
                self.assertEqual(self.client.post('/dashboard/orders/new-manual/',data).status_code,302);self.assertEqual(Order.objects.count(),before+1)

    def test_corrupt_indexes_or_management_never_silently_drop_rows(self):
        for mode in ['prefix','outside','leading_zero','negative','missing','overmax']:
            data=self.payload(['CF03-360']);before=Order.objects.count()
            if mode=='prefix':data['lines-__prefix__-variant']=ProductVariant.objects.get(sku='TE02-700').pk;data['lines-__prefix__-quantity']=1
            elif mode=='outside':data['lines-3-variant']=ProductVariant.objects.get(sku='TE02-700').pk;data['lines-3-quantity']=1
            elif mode in ['leading_zero','negative']:
                index='00' if mode=='leading_zero' else '-1'
                data[f'lines-{index}-variant']=ProductVariant.objects.get(sku='TE02-700').pk;data[f'lines-{index}-quantity']=1
            elif mode=='missing':data.pop('lines-TOTAL_FORMS')
            else:data['lines-TOTAL_FORMS']='11'
            response=self.client.post('/dashboard/orders/new-manual/',data);self.assertEqual(response.status_code,200);self.assertEqual(Order.objects.count(),before)
            self.assertFalse(response.context['lines'].is_valid())

    def test_invalid_line_preserved_and_deleted_line_handled(self):
        data=self.payload(['CF03-360','TE02-700','TE01-700']);data['lines-1-quantity']='0';before=Order.objects.count()
        response=self.client.post('/dashboard/orders/new-manual/',data);self.assertEqual(response.status_code,200);self.assertEqual(Order.objects.count(),before)
        self.assertEqual(str(response.context['lines'][2]['variant'].value()),str(data['lines-2-variant']))
        self.assertTrue(response.context['lines'][1].errors)
        data['lines-1-DELETE']='on';response=self.client.post('/dashboard/orders/new-manual/',data);self.assertEqual(response.status_code,302)
        self.assertEqual(Order.objects.get(idempotency_key=data['idempotency_key']).items.count(),2)

    def test_multi_item_inventory_and_cash_exact_once(self):
        data=self.payload(['CF03-360','TE02-700','TE01-700'],[2,1,3]);stock={i.pk:balance(i) for i in Ingredient.objects.all()}
        self.client.post('/dashboard/orders/new-manual/',data);o=Order.objects.select_related('payment').get(idempotency_key=data['idempotency_key'])
        self.assertFalse(StockMovement.objects.filter(order=o).exists());expected=defaultdict(int)
        for item in o.items.all():
            for line in item.recipe_snapshot:expected[line['ingredient_id']]+=Decimal(line['quantity'])*item.quantity
        staff_command(self.staff,o.public_code,'cash',version(o));o=Order.objects.select_related('payment').get(pk=o.pk)
        staff_command(self.staff,o.public_code,'start',version(o));self.assertEqual({i.pk:balance(i) for i in Ingredient.objects.all()},{k:v-expected[k] for k,v in stock.items()})
        before=list(StockMovement.objects.filter(order=o).values());self.assertEqual(o.payment.events.filter(event_key='cash_demo').count(),1)
        with self.assertRaises(ValidationError):staff_command(self.staff,o.public_code,'start',version(o))
        self.assertEqual(before,list(StockMovement.objects.filter(order=o).values()))
        self.client.force_login(self.staff);html=self.client.get('/dashboard/kitchen/').content.decode()
        for sku in ['CF03-360','TE02-700','TE01-700']:self.assertIn(sku,html)

    def test_missing_bom_on_last_line_rolls_back_all(self):
        data=self.payload(['CF03-360','TE02-700','TE01-700']);RecipeLine.objects.filter(variant__sku='TE01-700').delete();before=Order.objects.count()
        response=self.client.post('/dashboard/orders/new-manual/',data);self.assertEqual(response.status_code,200);self.assertEqual(Order.objects.count(),before)


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class RefundRaceTests(TransactionTestCase):
    def test_two_admins_cannot_confirm_same_refund_twice(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import connections
        load_compatibility_fixture()
        self.buyer=create_role_user('refund-race-buyer','CUSTOMER')
        a=create_role_user('refund-race-admin-a','ADMIN');b=create_role_user('refund-race-admin-b','ADMIN')
        o=RefundPOSTests.paid(self);transition_order(self.buyer,o.public_code,'CANCELLED');barrier=Barrier(2)
        def run(admin):
            try:
                barrier.wait(timeout=10)
                try:refund_mock(admin,o.public_code,strict=True);return 'confirmed'
                except ValidationError:return 'rejected'
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(run,[a,b]))
        self.assertCountEqual(result,['confirmed','rejected'])
        self.assertEqual(Payment.objects.get(order=o).status,'REFUNDED')
        self.assertEqual(o.payment.events.filter(event_key='mock_refund').count(),1)
