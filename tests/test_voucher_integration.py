"""QA regression for integrated campaign editing, visibility and customer eligibility."""
from django.test import TestCase, Client, override_settings
from django.contrib.admin.models import LogEntry
from django.utils import timezone
from django.core.exceptions import ValidationError
from commerce import vouchers
from commerce.models import VoucherUseV2
from tests.test_vouchers_v2 import Helpers, fixture, SETTINGS


@override_settings(**SETTINGS)
class VoucherIntegrationTests(Helpers, TestCase):
    @classmethod
    def setUpTestData(cls):
        fixture(cls)

    def data_for(self, voucher, **changes):
        data = dict(code=voucher.code, kind=voucher.kind, amount=voucher.amount,
                    min_subtotal=voucher.min_subtotal, max_uses=voucher.max_uses,
                    starts_at=voucher.starts_at.strftime('%Y-%m-%dT%H:%M'),
                    ends_at=voucher.ends_at.strftime('%Y-%m-%dT%H:%M'),
                    is_active='on', audience='PRIVATE')
        from commerce.voucher_management import version
        data.update({'version':version(voucher,self.admin),'alloc-TOTAL_FORMS':'0','alloc-INITIAL_FORMS':'0'})
        data.update(changes)
        return data

    def test_admin_edit_pause_and_history_preserved(self):
        campaign = self.voucher()
        order = self.place(voucher=campaign.voucher_id)
        before = list(VoucherUseV2.objects.values())
        self.client.force_login(self.admin)
        path = f'/dashboard/vouchers/{campaign.pk}/'
        response = self.client.post(path, self.data_for(campaign.voucher, amount=8000, is_active=''))
        self.assertEqual(response.status_code, 302)
        campaign.refresh_from_db();campaign.voucher.refresh_from_db();order.refresh_from_db()
        self.assertEqual(campaign.audience, 'PUBLIC')
        self.assertEqual(campaign.voucher.amount, 8000)
        self.assertFalse(campaign.voucher.is_active)
        self.assertEqual(order.discount, 5000)
        self.assertEqual(list(VoucherUseV2.objects.values()), before)
        self.assertEqual(LogEntry.objects.get().user_id, self.admin.pk)
        response = self.client.get(path)
        self.assertContains(response, str(order.public_code))
        self.assertContains(response, '5.000')

    def test_invalid_edit_quota_and_dates_leave_data_unchanged(self):
        campaign = self.voucher()
        self.place(voucher=campaign.voucher_id)
        self.client.force_login(self.admin)
        path = f'/dashboard/vouchers/{campaign.pk}/'
        for changes in ({'max_uses':0}, {'ends_at':'2000-01-01T00:00'}, {'amount':-1}):
            self.assertEqual(self.client.post(path,self.data_for(campaign.voucher,**changes)).status_code,200)
            campaign.voucher.refresh_from_db()
            self.assertEqual(campaign.voucher.amount,5000)
            self.assertTrue(campaign.voucher.is_active)
        self.assertFalse(LogEntry.objects.exists())

    def test_filters_and_private_detail_rbac_csrf_flag(self):
        public=self.voucher(code='PUBLICINTEGRATION')
        private=self.voucher('PRIVATE',code='PRIVATEINTEGRATION',is_active=False)
        path=f'/dashboard/vouchers/{private.pk}/'
        for actor in (self.staff,self.user):
            self.client.force_login(actor)
            self.assertEqual(self.client.get(path).status_code,403)
            self.assertEqual(self.client.post(path,self.data_for(private.voucher)).status_code,403)
        self.client.force_login(self.admin)
        response=self.client.get('/dashboard/vouchers/',{'q':'PRIVATEINTEGRATION','audience':'PRIVATE','status':'inactive'})
        self.assertEqual([row.pk for row in response.context['campaigns']], [private.pk])
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin)
        self.assertEqual(csrf.post(path,self.data_for(private.voucher)).status_code,403)
        with override_settings(NAU_VOUCHERS_V2_ENABLED=False):
            self.assertEqual(self.client.get(path).status_code,404)
        self.assertEqual(self.client.get('/dashboard/vouchers/999999/').status_code,404)

    def test_pending_or_native_staff_cannot_use_or_receive_new_vouchers(self):
        campaign=self.voucher()
        self.profile.email_verified_at=None;self.profile.origin='STAFF';self.profile.save()
        self.assertEqual(vouchers.available(self.user,'WEB'),[])
        with self.assertRaisesMessage(ValidationError,'Campaign mới'):
            vouchers.quote_selection(campaign.voucher_id,self.user,'WEB',28000)
        self.profile.email_verified_at=timezone.now();self.profile.save()
        self.user.is_staff=True;self.user.save()
        self.assertEqual(vouchers.available(self.user,'WEB'),[])
        with self.assertRaisesMessage(ValidationError,'Campaign mới'):
            vouchers.quote_selection(campaign.voucher_id,self.user,'WEB',28000)
        private=self.voucher('PRIVATE')
        with self.assertRaises(ValidationError):
            vouchers.grant_uses(self.admin,private.pk,self.user.pk,1,'Wrong identity')

    def test_remaining_grants_and_history_read_only(self):
        campaign=self.voucher('PRIVATE')
        vouchers.grant_uses(self.admin,campaign.pk,self.user.pk,2,'QA integration')
        self.place(voucher=campaign.voucher_id)
        before=list(VoucherUseV2.objects.values())
        self.client.force_login(self.admin)
        response=self.client.get(f'/dashboard/vouchers/{campaign.pk}/')
        self.assertEqual(response.context['grants'][0].remaining,1)
        self.assertEqual(list(VoucherUseV2.objects.values()),before)
