"""Versioned voucher policy, trusted counter identity, and immutable legacy history."""
import uuid
from datetime import timedelta
from unittest import skipUnless
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, connections, transaction, IntegrityError
from django.test import TestCase, TransactionTestCase, override_settings, Client
from django.utils import timezone
from catalog import customer_accounts as accounts
from catalog.customer_models import CounterConsent
from commerce.models import Cart, Order, Voucher, VoucherCampaign, VoucherGrant, VoucherGrantAudit, VoucherRedemption, VoucherUseV2, RecipeLine
from commerce import vouchers
from commerce.services import add_item, quote_cart, place_order, transition_order, simulate_payment, refund_mock
from commerce.operations import manual_order, quote_manual
from tests import test_customer_accounts as account_fixtures
EMAIL_SETTINGS = account_fixtures.EMAIL_SETTINGS
PASSWORD = account_fixtures.PASSWORD
SETTINGS = dict(EMAIL_SETTINGS, NAU_VOUCHERS_V2_ENABLED=True)

def fixture(cls):
    account_fixtures.CounterCustomerTests.setUpTestData.__func__(cls)
    cls.user = cls.profile.user
    cls.admin = User.objects.create_user('voucher-admin', password=PASSWORD)
    cls.admin.groups.add(Group.objects.get_or_create(name='ADMIN')[0])

class Helpers:

    def voucher(self, audience='PUBLIC', **changes):
        values = dict(code='V' + uuid.uuid4().hex[:15], kind='FIXED', amount=5000, min_subtotal=0, starts_at=timezone.now() - timedelta(days=1), ends_at=timezone.now() + timedelta(days=1))
        values.update(changes)
        v = Voucher.objects.create(**values)
        return VoucherCampaign.objects.create(voucher=v, audience=audience, created_by=self.admin)

    def cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        add_item(cart, self.variant.pk, 1)
        return cart

    def data(self, **updates):
        values = dict(customer_name='Khách fixture', phone='0901234567', fulfillment='PICKUP', payment_method='MOCK_ONLINE', idempotency_key=uuid.uuid4())
        values.update(updates)
        return values

    def place(self, cart=None, **updates):
        with patch('commerce.operations.scheduled_slot', return_value=timezone.now() + timedelta(hours=1)):
            return place_order(self.user, cart or self.cart(), self.data(**updates))

    def counter_data(self, **updates):
        values = dict(channel='COUNTER', phone='0901234567', customer_name='Khách fixture', idempotency_key=uuid.uuid4(), customer_selection_context='voucher-session', confirm_customer=True, customer_selection=accounts.selection_for(self.profile, self.staff, session_context='voucher-session'), customer_consent=accounts.issue_counter_consent(self.user, PASSWORD))
        values.update(updates)
        return values

    def lines(self):
        return [dict(variant=self.variant, quantity=1, options=[])]

@override_settings(**SETTINGS)
class VoucherV2Tests(Helpers, TestCase):

    @classmethod
    def setUpTestData(cls):
        fixture(cls)

    def test_public_once_and_cancel_does_not_restore_even_flag_off(self):
        campaign = self.voucher()
        order = self.place(voucher=campaign.voucher_id)
        self.assertEqual(order.discount, 5000)
        self.assertEqual(order.payment.amount, 23000)
        with override_settings(NAU_VOUCHERS_V2_ENABLED=False):
            transition_order(self.user, order.public_code, 'CANCELLED')
        self.assertTrue(VoucherRedemption.objects.get(order=order).is_active)
        with self.assertRaises(ValidationError):
            self.place(voucher=campaign.voucher_id)
        self.assertEqual(VoucherUseV2.objects.get().snapshot['discount'], 5000)

    def test_payment_failure_and_refund_do_not_release_new_quota(self):
        campaign = self.voucher()
        order = self.place(voucher=campaign.voucher_id)
        simulate_payment(self.user, order.payment.token, False)
        self.assertEqual(campaign.uses.count(), 1)
        simulate_payment(self.user, order.payment.token, True)
        transition_order(self.user, order.public_code, 'CANCELLED')
        refund_mock(self.admin, order.public_code, strict=True)
        self.assertEqual(campaign.uses.count(), 1)
        with self.assertRaises(ValidationError):
            self.place(voucher=campaign.voucher_id)

    def test_private_grants_admin_only_and_audited(self):
        campaign = self.voucher('PRIVATE')
        for actor in (self.staff, self.user):
            with self.assertRaises(PermissionDenied):
                vouchers.grant_uses(actor, campaign.pk, self.user.pk, 2, 'Kiểm thử')
        with self.assertRaises(ValidationError):
            self.place(voucher=campaign.voucher_id)
        grant = vouchers.grant_uses(self.admin, campaign.pk, self.user.pk, 2, 'Khách được cấp')
        self.place(voucher=campaign.voucher_id)
        self.place(voucher=campaign.voucher_id)
        grant.refresh_from_db()
        self.assertEqual((grant.used, grant.allocated), (2, 2))
        with self.assertRaises(ValidationError):
            self.place(voucher=campaign.voucher_id)
        self.assertEqual(VoucherGrantAudit.objects.get().after, 2)
        vouchers.grant_uses(self.admin, campaign.pk, self.user.pk, 1, 'Cấp thêm')
        self.place(voucher=campaign.voucher_id)
        self.assertEqual(list(campaign.uses.order_by('ordinal').values_list('ordinal', flat=True)), [1, 2, 3])

    def test_no_quota_consumed_on_quote_or_failed_order_or_idempotent_retry(self):
        campaign = self.voucher()
        cart = self.cart()
        for i in range(3):
            self.assertEqual(quote_cart(cart, self.user, voucher_id=campaign.voucher_id)['discount'], 5000)
        self.assertFalse(VoucherRedemption.objects.exists())
        with patch('commerce.operations.check_order_inventory', side_effect=ValidationError('BOM thiếu')):
            with self.assertRaises(ValidationError):
                self.place(cart, voucher=campaign.voucher_id)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(campaign.uses.exists())
        data = self.data(voucher=campaign.voucher_id)
        with patch('commerce.operations.scheduled_slot', return_value=timezone.now() + timedelta(hours=1)):
            first = place_order(self.user, cart, data)
            second = place_order(self.user, cart, data)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(campaign.uses.count(), 1)

    def test_legacy_policy_preserved_and_never_automatically_marked(self):
        campaign = self.voucher()
        voucher = campaign.voucher
        campaign.delete()
        before = Voucher.objects.values().get(pk=voucher.pk)
        order = self.place(voucher_code=voucher.code)
        transition_order(self.user, order.public_code, 'CANCELLED')
        self.assertFalse(VoucherRedemption.objects.get(order=order).is_active)
        self.place(voucher=voucher.pk)
        self.assertEqual(Voucher.objects.values().get(pk=voucher.pk), before)
        self.assertFalse(VoucherUseV2.objects.exists())

    def test_new_campaign_never_falls_back_to_legacy_code_even_flag_off(self):
        campaign = self.voucher()
        cart = self.cart()
        for state in (True, False):
            with override_settings(NAU_VOUCHERS_V2_ENABLED=state):
                with self.assertRaises(ValidationError):
                    quote_cart(cart, self.user, voucher_code=campaign.voucher.code)

    def test_one_voucher_only_and_invalid_selections(self):
        campaign = self.voucher()
        cart = self.cart()
        for value in ('²', '-1', '1,2', '9' * 1000, '0', ['1', '2']):
            with self.assertRaises(ValidationError):
                quote_cart(cart, self.user, voucher_id=value)
        with self.assertRaises(ValidationError):
            quote_cart(cart, self.user, voucher_id=campaign.voucher_id, voucher_code='OTHER')

    def test_counter_quote_does_not_consume_proof_and_final_uses_discounted_payment(self):
        campaign = self.voucher('PRIVATE')
        vouchers.grant_uses(self.admin, campaign.pk, self.user.pk, 1, 'Fixture')
        data = self.counter_data(voucher=campaign.voucher_id)
        for i in range(3):
            self.assertEqual(quote_manual(self.staff, data, self.lines())['total'], 23000)
        self.assertIsNone(CounterConsent.objects.get(user=self.user).used_at)
        self.assertFalse(campaign.uses.exists())
        with patch('commerce.operations.scheduled_slot', return_value=timezone.now() + timedelta(hours=1)):
            order = manual_order(self.staff, data, self.lines())
        self.assertEqual(order.total, 23000)
        self.assertEqual(order.payment.amount, 23000)
        self.assertIsNotNone(CounterConsent.objects.get(user=self.user).used_at)
        with self.assertRaises(ValidationError):
            quote_manual(self.staff, data, self.lines())

    def test_public_counter_use_prevents_web_reuse_and_guest_app_denied(self):
        campaign = self.voucher()
        data = self.counter_data(voucher=campaign.voucher_id)
        with patch('commerce.operations.scheduled_slot', return_value=timezone.now() + timedelta(hours=1)):
            manual_order(self.staff, data, self.lines())
        with self.assertRaises(ValidationError):
            self.place(voucher=campaign.voucher_id)
        for changes in ({'channel': 'APP', 'external_reference': 'APP-fixture'}, {'customer_selection': ''}):
            data = dict(channel='COUNTER', customer_name='Guest', idempotency_key=uuid.uuid4(), voucher=campaign.voucher_id)
            data.update(changes)
            with self.assertRaises(ValidationError):
                manual_order(self.staff, data, self.lines())
        self.assertEqual(vouchers.available(self.user, 'APP'), [])

    def test_limits_expiry_stacking_caps_and_inactive_accounts(self):
        campaign = self.voucher(kind='PERCENT', amount=50, cap=3000)
        self.assertEqual(quote_cart(self.cart(), self.user, voucher_id=campaign.voucher_id)['discount'], 3000)
        for change in ({'min_subtotal': 999999}, {'is_active': False}, {'ends_at': timezone.now() - timedelta(seconds=1)}):
            for k, v in change.items():
                setattr(campaign.voucher, k, v)
            campaign.voucher.save()
            with self.assertRaises(ValidationError):
                quote_cart(Cart.objects.get(user=self.user), self.user, voucher_id=campaign.voucher_id)
        with self.assertRaises(ValidationError):
            vouchers.grant_uses(self.admin, campaign.pk, self.staff.pk, 1, 'Sai role')

    def test_http_quote_rbac_csrf_private_visibility_and_no_manual_code(self):
        campaign = self.voucher('PRIVATE')
        self.cart()
        self.assertEqual(self.client.post('/checkout/voucher-quote/').status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get('/checkout/')
        self.assertNotContains(response, 'Tính lại giá')
        self.assertNotContains(response, 'name="voucher_code"')
        self.assertNotContains(self.client.get('/promotions/'), campaign.voucher.code)
        self.assertNotContains(self.client.get('/'), campaign.voucher.code)
        response = self.client.post('/checkout/voucher-quote/', {'voucher': campaign.voucher_id})
        self.assertEqual(response.status_code, 400)
        for data in ({'voucher_code': campaign.voucher.code}, {'voucher': ['1', '2']}):
            self.assertEqual(self.client.post('/checkout/voucher-quote/', data).status_code, 400)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.user)
        self.assertEqual(csrf.post('/checkout/voucher-quote/').status_code, 403)
        for path in ('/dashboard/vouchers/', '/dashboard/orders/voucher-quote/'):
            self.assertEqual(self.client.post(path).status_code, 403)
        self.assertFalse(VoucherRedemption.objects.exists())

    def test_admin_campaign_creation_and_grants_forms(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/dashboard/vouchers/').status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/dashboard/vouchers/').status_code, 200)
        from tests.test_unified_voucher_management import data,recipients
        response = self.client.post('/dashboard/vouchers/', recipients(data(self.admin, action='campaign',code='ADMINNEW', audience='PRIVATE'),[(self.user,1,0)]))
        self.assertEqual(response.status_code, 302)
        campaign = VoucherCampaign.objects.get(voucher__code='ADMINNEW')
        response = self.client.post('/dashboard/vouchers/', dict(action='grant', campaign=campaign.pk, user=self.user.pk, extra=2, reason='Đợt QA'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(VoucherGrant.objects.get().allocated, 3)

    def test_http_checkout_selected_voucher_ignores_forged_total(self):
        campaign = self.voucher()
        self.cart()
        self.client.force_login(self.user)
        self.client.get('/checkout/')
        data = self.data(voucher=str(campaign.voucher_id), total=1, discount=999999,
                         accept_demo='on', action='place', idempotency_key=self.client.session['checkout_key'])
        with patch('commerce.operations.scheduled_slot', return_value=timezone.now()+timedelta(hours=1)):
            response = self.client.post('/checkout/', data)
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual((order.subtotal,order.discount,order.total),(28000,5000,23000))

    def test_counter_quote_endpoint_uses_session_not_post_and_keeps_proof_unused(self):
        campaign = self.voucher('PRIVATE')
        vouchers.grant_uses(self.admin,campaign.pk,self.user.pk,1,'HTTP fixture')
        self.client.force_login(self.staff)
        self.client.post('/dashboard/customers/lookup/', {'phone':'0901234567'})
        data = dict(channel='COUNTER', phone='0901234567', confirm_customer='on',
                    customer_selection=self.client.session['counter_customer_selection'],
                    customer_consent=accounts.issue_counter_consent(self.user,PASSWORD), voucher=str(campaign.voucher_id),
                    **{'lines-TOTAL_FORMS':'1','lines-INITIAL_FORMS':'0','lines-0-variant':str(self.variant.pk),'lines-0-quantity':'1'})
        response = self.client.post('/dashboard/orders/voucher-quote/',data)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json()['total'],23000)
        self.assertIsNone(CounterConsent.objects.get(user=self.user).used_at)
        other=Client();other.force_login(self.staff)
        data['customer_selection_context']=self.client.session['counter_selection_context']
        self.assertEqual(other.post('/dashboard/orders/voucher-quote/',data).status_code,400)
        data.update(channel='APP',customer_selection='',customer_consent='',confirm_customer='')
        self.assertEqual(self.client.post('/dashboard/orders/voucher-quote/',data).status_code,400)
        self.assertFalse(Order.objects.exists())

    def test_private_account_scope_global_limit_and_sale_stacking(self):
        campaign=self.voucher('PRIVATE',max_uses=1)
        vouchers.grant_uses(self.admin,campaign.pk,self.user.pk,2,'Scope fixture')
        other=User.objects.create_user('other-voucher-customer');other.groups.add(Group.objects.get(name='CUSTOMER'))
        self.assertEqual(vouchers.available(other,'WEB'),[])
        with self.assertRaises(ValidationError):vouchers.quote_selection(campaign.voucher_id,other,'WEB',28000)
        with self.assertRaises(ValidationError):vouchers.quote_selection(campaign.voucher_id,self.user,'WEB',28000,True)
        self.place(voucher=campaign.voucher_id)
        with self.assertRaises(ValidationError):self.place(voucher=campaign.voucher_id)
        self.assertEqual(campaign.uses.count(),1)

@skipUnless(connection.vendor == 'postgresql', 'PostgreSQL QA required for real row-lock concurrency')
@override_settings(**SETTINGS)
class VoucherRaceTests(Helpers, TransactionTestCase):

    def setUp(self):
        fixture(self.__class__)

    def race(self, campaign):
        barrier = Barrier(2)

        def attempt(i):
            try:
                barrier.wait(timeout=10)
                with transaction.atomic():
                    voucher, discount, policy = vouchers.quote_selection(campaign.voucher_id, self.user, 'WEB', 28000)
                    order = Order.objects.create(user=self.user, customer_name='Race fixture', phone='0901234567', subtotal=28000, discount=discount, total=28000 - discount, idempotency_key=uuid.uuid4())
                    vouchers.record_use(order, self.user, voucher, policy)
                return 'created'
            except ValidationError:
                return 'quota'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertCountEqual(results, ['created', 'quota'])
        self.assertEqual(campaign.uses.count(), 1)

    def test_public_once_race(self):
        self.race(self.voucher())

    def test_private_last_grant_race(self):
        campaign = self.voucher('PRIVATE')
        vouchers.grant_uses(self.admin, campaign.pk, self.user.pk, 1, 'Race fixture')
        self.race(campaign)

    def test_public_web_counter_race(self):
        campaign = self.voucher()
        cart = self.cart()
        data = self.counter_data(voucher=campaign.voucher_id)
        barrier = Barrier(2)

        def attempt(channel):
            try:
                barrier.wait(timeout=10)
                with patch('commerce.operations.scheduled_slot', return_value=timezone.now() + timedelta(hours=1)):
                    if channel == 'WEB':
                        place_order(self.user, cart, self.data(voucher=campaign.voucher_id))
                    else:
                        manual_order(self.staff, data, self.lines())
                return 'created'
            except ValidationError:
                return 'quota'
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, ['WEB', 'COUNTER']))
        self.assertCountEqual(results, ['created', 'quota'])
        self.assertEqual(campaign.uses.count(), 1)

@override_settings(**SETTINGS)
class VoucherMigrationTests(TransactionTestCase):

    def test_schema_upgrade_preserves_legacy_vouchers_redemptions_and_totals(self):
        from django.db.migrations.executor import MigrationExecutor
        previous = [('commerce', '0004_demo_delivery'), ('catalog', '0005_counterconsent_countercustomerlink_customerprofile')]
        executor = MigrationExecutor(connection)
        executor.migrate(previous)
        try:
            apps = executor.loader.project_state(previous).apps
            user = apps.get_model('auth', 'User').objects.create(username='old-voucher-user')
            order = apps.get_model('commerce', 'Order').objects.create(user=user, customer_name='Lịch sử QA', phone='không sửa', subtotal=28000, discount=5000, total=23000, status='CANCELLED', idempotency_key=uuid.uuid4())
            voucher = apps.get_model('commerce', 'Voucher').objects.create(code='OLD-QA', kind='FIXED', amount=5000, starts_at=timezone.now() - timedelta(days=1), ends_at=timezone.now() + timedelta(days=1))
            apps.get_model('commerce', 'VoucherRedemption').objects.create(order=order, voucher=voucher, user=user, is_active=False)
            names = ('Order', 'Voucher', 'VoucherRedemption')
            before = {name: list(apps.get_model('commerce', name).objects.values()) for name in names}
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
            for name in names:
                self.assertEqual(list(executor.loader.project_state(executor.loader.graph.leaf_nodes()).apps.get_model('commerce', name).objects.values()), before[name])
            self.assertFalse(VoucherCampaign.objects.exists())
            self.assertFalse(VoucherUseV2.objects.exists())
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(executor.loader.graph.leaf_nodes())
