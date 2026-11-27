from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.test import TestCase, TransactionTestCase, override_settings, Client
from django.contrib.auth.models import User, Group, Permission
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connections, close_old_connections, connection
from unittest import skipUnless
from django.utils import timezone
from commerce import vouchers
from commerce.models import Voucher, VoucherCampaign, VoucherGrant, VoucherGrantAudit, VoucherRedemption
from commerce.voucher_management import VoucherForm, AllocationSet, save_voucher, version
from tests.test_vouchers_v2 import fixture, Helpers, SETTINGS


def data(actor, voucher=None, **changes):
    values=dict(code=voucher.code if voucher else 'UNIFIED',kind='FIXED',amount=5000,min_subtotal=0,max_uses=10,
        starts_at='2020-01-01T00:00',ends_at='2030-01-01T00:00',is_active='on',audience='PUBLIC',reason='Cấp theo yêu cầu',version=version(voucher,actor),**{'alloc-TOTAL_FORMS':'0','alloc-INITIAL_FORMS':'0'})
    values.update(changes);return values


def recipients(values, rows):
    values['alloc-TOTAL_FORMS']=str(len(rows))
    for i,(user,allocated,expected) in enumerate(rows):
        values.update({f'alloc-{i}-selected':'on',f'alloc-{i}-customer_id':str(user.pk),f'alloc-{i}-allocated':str(allocated),f'alloc-{i}-expected':str(expected)})
    return values


def save(actor,values,voucher=None):
    form=VoucherForm(values,instance=voucher,actor=actor);forms=AllocationSet(values,prefix='alloc')
    assert form.is_valid(),form.errors.as_text()
    assert forms.is_valid(),forms.errors
    return save_voucher(actor,form,forms)


@override_settings(**SETTINGS)
class UnifiedVoucherTests(Helpers,TestCase):
    @classmethod
    def setUpTestData(cls):fixture(cls)

    def test_create_private_and_grant_in_one_transaction(self):
        v=save(self.admin,recipients(data(self.admin,audience='PRIVATE'),[(self.user,3,0)]))
        grant=VoucherGrant.objects.get(campaign__voucher=v)
        self.assertEqual(grant.allocated,3)
        self.assertEqual(VoucherGrantAudit.objects.get().after,3)
        self.assertEqual(vouchers.quote_selection(v.pk,self.user,'WEB',28000)[1],5000)
        other=User.objects.create_user('not-granted');other.groups.add(Group.objects.get(name='CUSTOMER'))
        self.assertEqual(vouchers.available(other,'WEB'),[])
        with self.assertRaises(ValidationError):vouchers.quote_selection(v.pk,other,'WEB',28000)

    def test_invalid_second_recipient_rolls_back_all(self):
        before=Voucher.objects.count()
        with self.assertRaises(ValidationError):save(self.admin,recipients(data(self.admin,audience='PRIVATE'),[(self.user,2,0),(self.staff,1,0)]))
        self.assertEqual(Voucher.objects.count(),before)
        self.assertFalse(VoucherGrant.objects.exists())

    def test_private_requires_verified_and_public_rejects_allocations(self):
        self.profile.email_verified_at=None;self.profile.save()
        with self.assertRaises(ValidationError):save(self.admin,recipients(data(self.admin,audience='PRIVATE'),[(self.user,1,0)]))
        with self.assertRaises(ValidationError):save(self.admin,recipients(data(self.admin,code='PUBLICX'),[(self.user,1,0)]))
        with self.assertRaises(ValidationError):save(self.admin,data(self.admin,audience='PRIVATE'))

    def test_absolute_allocation_audit_stale_replay_and_used_floor(self):
        v=save(self.admin,recipients(data(self.admin,audience='PRIVATE'),[(self.user,3,0)]))
        order=self.place(voucher=v.pk);g=VoucherGrant.objects.get(campaign__voucher=v)
        update=recipients(data(self.admin,v),[(self.user,2,3)])
        save(self.admin,update,v);g.refresh_from_db()
        self.assertEqual((g.allocated,g.used),(2,1))
        with self.assertRaises(ValidationError):save(self.admin,update,Voucher.objects.get(pk=v.pk))
        v.refresh_from_db()
        with self.assertRaises(ValidationError):save(self.admin,recipients(data(self.admin,v),[(self.user,0,2)]),v)
        self.assertEqual(VoucherGrantAudit.objects.count(),2)
        order.refresh_from_db();self.assertEqual(order.discount,5000)

    def test_unchanged_browser_datetime_preserves_original_precision(self):
        v=save(self.admin,data(self.admin))
        v.starts_at=v.starts_at.replace(microsecond=123456);v.ends_at=v.ends_at.replace(microsecond=987654);v.save()
        before=(v.starts_at,v.ends_at)
        values=data(self.admin,v,starts_at=timezone.localtime(v.starts_at).strftime('%Y-%m-%dT%H:%M:%S'),ends_at=timezone.localtime(v.ends_at).strftime('%Y-%m-%dT%H:%M:%S'))
        save(self.admin,values,v);v.refresh_from_db()
        self.assertEqual((v.starts_at,v.ends_at),before)

    def test_legacy_policy_and_redemption_are_not_converted(self):
        v=self.voucher().voucher
        VoucherCampaign.objects.filter(voucher=v).delete()
        before=v.per_user_limit
        order=self.place(voucher=v.pk)
        redemption_before=list(VoucherRedemption.objects.values())
        self.client.force_login(self.admin)
        values=data(self.admin,v,legacy_limit=before,amount=6000)
        response=self.client.post(f'/dashboard/vouchers/record/{v.pk}/',values)
        self.assertEqual(response.status_code,302)
        self.assertFalse(VoucherCampaign.objects.filter(voucher=v).exists())
        v.refresh_from_db();self.assertEqual(v.per_user_limit,before)
        self.assertEqual(list(VoucherRedemption.objects.values()),redemption_before)
        order.refresh_from_db();self.assertEqual(order.discount,5000)

    def test_admin_search_rbac_csrf_verified_only(self):
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin)
        self.assertEqual(csrf.post('/dashboard/vouchers/customers/search/',{'q':'Khách'}).status_code,403)
        self.client.force_login(self.admin)
        r=self.client.post('/dashboard/vouchers/customers/search/',{'q':'0901234567'})
        self.assertEqual(r.status_code,200)
        self.assertEqual([u['id'] for u in r.json()['customers']],[self.user.pk])
        self.assertEqual(r['Cache-Control'],'no-store')
        for user in [self.staff,self.user]:
            self.client.force_login(user)
            self.assertEqual(self.client.post('/dashboard/vouchers/customers/search/',{'q':'Khách'}).status_code,403)
            self.assertEqual(self.client.get('/dashboard/vouchers/new/').status_code,403)

    def test_one_listing_includes_all_policies_and_filters(self):
        v=self.voucher(code='OLD').voucher;VoucherCampaign.objects.filter(voucher=v).delete()
        self.voucher(code='PUB');self.voucher('PRIVATE',code='VIP')
        self.client.force_login(self.admin)
        response=self.client.get('/dashboard/vouchers/')
        self.assertEqual(len(response.context['voucher_page']),3)
        self.assertEqual(len(self.client.get('/dashboard/vouchers/',{'audience':'LEGACY'}).context['voucher_page']),1)
        self.assertEqual(len(self.client.get('/dashboard/vouchers/',{'audience':'PRIVATE'}).context['voucher_page']),1)

    def test_search_reloads_real_baseline_for_existing_grants(self):
        campaign=self.voucher('PRIVATE');vouchers.grant_uses(self.admin,campaign.pk,self.user.pk,3,'Baseline')
        self.place(voucher=campaign.voucher_id);self.client.force_login(self.admin)
        response=self.client.post('/dashboard/vouchers/customers/search/',{'q':self.user.username,'voucher_id':campaign.voucher_id})
        customer=response.json()['customers'][0]
        self.assertEqual((customer['has_grant'],customer['allocated'],customer['used']),(True,3,1))
        voucher=campaign.voucher
        save(self.admin,recipients(data(self.admin,voucher),[(self.user,4,customer['allocated'])]),voucher)
        self.assertEqual(VoucherGrant.objects.get().allocated,4)
        for invalid in ['²','-1','9'*30,'forged']:
            self.assertEqual(self.client.post('/dashboard/vouchers/customers/search/',{'q':'Khách','voucher_id':invalid}).status_code,400)

    def test_compat_grant_exact_replay_adds_once(self):
        campaign=self.voucher('PRIVATE');self.client.force_login(self.admin)
        payload={'action':'grant','campaign':campaign.pk,'user':self.user.pk,'extra':2,'reason':'Replay safe'}
        self.assertEqual(self.client.post('/dashboard/vouchers/',payload).status_code,302)
        self.assertEqual(self.client.post('/dashboard/vouchers/',payload).status_code,302)
        self.assertEqual(VoucherGrant.objects.get().allocated,2)
        self.assertEqual(VoucherGrantAudit.objects.count(),1)

    def test_compat_endpoint_cannot_grant_unverified_legacy_identity(self):
        campaign=self.voucher('PRIVATE');self.profile.origin='LEGACY';self.profile.email_verified_at=None;self.profile.save()
        self.client.force_login(self.admin)
        response=self.client.post('/dashboard/vouchers/',{'action':'grant','campaign':campaign.pk,'user':self.user.pk,'extra':1,'reason':'Không được cấp'})
        self.assertEqual(response.status_code,200)
        self.assertFalse(VoucherGrant.objects.exists())

    def test_backend_only_admin_and_new_scope_cannot_change(self):
        with self.assertRaises(PermissionDenied):save(self.staff,data(self.staff))
        v=save(self.admin,data(self.admin));self.client.force_login(self.admin)
        r=self.client.post(f'/dashboard/vouchers/record/{v.pk}/',data(self.admin,v,audience='PRIVATE'))
        self.assertEqual(r.status_code,302)
        self.assertEqual(VoucherCampaign.objects.get(voucher=v).audience,'PUBLIC')

    def test_native_read_only_admin_cannot_mutate_through_compat_post(self):
        self.admin.is_staff=True;self.admin.save(update_fields=['is_staff'])
        self.admin.user_permissions.add(Permission.objects.get(codename='view_voucher'))
        campaign=self.voucher('PRIVATE');self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin/commerce/voucher/').status_code,200)
        response=self.client.get(f'/admin/commerce/voucher/{campaign.voucher_id}/change/')
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,'>Lưu cấu hình</button>')
        response=self.client.post('/admin/commerce/voucher/',{'action':'grant','campaign':campaign.pk,'user':self.user.pk,'extra':2,'reason':'Không đủ quyền native'})
        self.assertEqual(response.status_code,403)
        self.assertEqual(self.client.post('/admin/commerce/voucher/',data(self.admin,action='campaign')).status_code,403)
        self.assertFalse(VoucherGrant.objects.exists())

    def test_multiple_verified_customers_have_independent_quotas(self):
        from catalog.customer_models import CustomerProfile
        second=User.objects.create_user('vip-second');second.groups.add(Group.objects.get(name='CUSTOMER'))
        CustomerProfile.objects.create(user=second,full_name='Khách thứ hai',phone='+84901234568',email='vipsecond@example.invalid',origin='PUBLIC',email_verified_at=timezone.now())
        v=save(self.admin,recipients(data(self.admin,audience='PRIVATE'),[(self.user,2,0),(second,5,0)]))
        self.assertEqual(list(VoucherGrant.objects.filter(campaign__voucher=v).order_by('user_id').values_list('allocated',flat=True)),[2,5])
        self.assertEqual(VoucherGrantAudit.objects.count(),2)

    def test_duplicate_create_has_no_partial_grants(self):
        values=recipients(data(self.admin,audience='PRIVATE'),[(self.user,2,0)])
        save(self.admin,values)
        form=VoucherForm(values,actor=self.admin)
        self.assertFalse(form.is_valid())
        self.assertEqual(Voucher.objects.filter(code='UNIFIED').count(),1)
        self.assertEqual(VoucherGrant.objects.count(),1)


@skipUnless(connection.vendor=='postgresql','PostgreSQL row locks required')
@override_settings(**SETTINGS)
class UnifiedVoucherRaceTests(Helpers,TransactionTestCase):
    def setUp(self):fixture(type(self))

    def run_race(self,functions):
        barrier=Barrier(2)
        def run(fn):
            close_old_connections()
            try:barrier.wait(timeout=10);return fn()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(run,functions))

    def test_only_one_stale_allocation_update_wins(self):
        v=save(self.admin,recipients(data(self.admin,audience='PRIVATE'),[(self.user,1,0)]))
        first=recipients(data(self.admin,v),[(self.user,2,1)]);second=recipients(data(self.admin,v),[(self.user,3,1)])
        def update(values):
            try:save(User.objects.get(pk=self.admin.pk),values,Voucher.objects.get(pk=v.pk));return 'saved'
            except ValidationError:return 'stale'
        results=self.run_race([lambda:update(first),lambda:update(second)])
        self.assertCountEqual(results,['saved','stale'])
        self.assertIn(VoucherGrant.objects.get().allocated,[2,3])
        self.assertEqual(VoucherGrantAudit.objects.count(),2)

    def test_duplicate_creation_race_rolls_back_loser(self):
        from django.db import IntegrityError
        values=recipients(data(self.admin,audience='PRIVATE'),[(self.user,2,0)])
        def create():
            actor=User.objects.get(pk=self.admin.pk)
            form=VoucherForm(values,actor=actor);fs=AllocationSet(values,prefix='alloc')
            if not form.is_valid() or not fs.is_valid():return 'duplicate'
            try:save_voucher(actor,form,fs);return 'created'
            except (ValidationError,IntegrityError):return 'duplicate'
        self.assertCountEqual(self.run_race([create,create]),['created','duplicate'])
        self.assertEqual(Voucher.objects.filter(code='UNIFIED').count(),1)
        self.assertEqual(VoucherGrant.objects.count(),1)

    def test_quota_reduction_cannot_race_below_consumed_uses(self):
        v=save(self.admin,recipients(data(self.admin,audience='PRIVATE'),[(self.user,1,0)]));cart=self.cart()
        values=recipients(data(self.admin,v),[(self.user,0,1)])
        def reduce():
            try:save(User.objects.get(pk=self.admin.pk),values,Voucher.objects.get(pk=v.pk));return 'reduced'
            except ValidationError:return 'floor'
        def consume():
            try:self.place(cart,voucher=v.pk);return 'order'
            except ValidationError:return 'blocked'
        result=self.run_race([reduce,consume]);grant=VoucherGrant.objects.get()
        self.assertLessEqual(grant.used,grant.allocated)
        self.assertTrue(set(result) in [{'reduced','blocked'},{'floor','order'}],result)
