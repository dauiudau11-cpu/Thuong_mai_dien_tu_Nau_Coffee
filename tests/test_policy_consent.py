import json,uuid
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase,Client,override_settings
from django.contrib.auth.models import User,Permission
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import connection,transaction,DatabaseError
from django.utils import timezone
from tests.test_vouchers_v2 import fixture,Helpers,SETTINGS,PASSWORD
from support.models import Policy,PolicyRevision,ConsentEvent
from support import policies

FLAGS=dict(SETTINGS,NAU_POLICY_CONSENT_ENABLED=True)

def published_fixture(cls):
    fixture(cls);cls.admin.is_staff=True;cls.admin.save(update_fields=['is_staff']);cls.admin.user_permissions.add(*Permission.objects.all())
    rows=json.loads(Path('docs/policies/NAU_POLICY_DRAFTS_2026-11-17.json').read_text())
    for row in rows:
        policy,_=Policy.objects.get_or_create(slug=row['slug'],defaults={'title':row['title'],'body':'Legacy body preserved'})
        revision=PolicyRevision.objects.create(policy=policy,version='qa-v1',title=row['title'],body=row['body'],effective_at=timezone.now()-timezone.timedelta(days=1),reviewed=True,review_note='Synthetic QA approval; not actual publication approval',created_by=cls.admin)
        policies.publish(cls.admin,revision.pk)


@override_settings(**FLAGS)
class PolicyConsentTests(Helpers,TestCase):
    @classmethod
    def setUpTestData(cls):published_fixture(cls)

    def token(self,path):
        response=self.client.get(path);self.assertEqual(response.status_code,200)
        return response.context['form']['policy_token'].value()

    def registration(self,**extra):
        data={'full_name':'Khách chính sách','phone':'0901234578','email':'policy@example.invalid','username':'policy-customer','password1':PASSWORD,'password2':PASSWORD,'policy_token':self.token('/accounts/register/'),'accept_terms':'on'};data.update(extra);return data

    def checkout_payload(self,**extra):
        self.cart();self.client.force_login(self.user);response=self.client.get('/checkout/');self.assertEqual(response.status_code,200)
        data=self.data(idempotency_key=response.context['form']['idempotency_key'].value(),policy_token=response.context['form']['policy_token'].value(),accept_demo='on',accept_order_terms='on');data.update(extra);return data

    def test_all_eleven_public_pages_links_and_legacy_aliases(self):
        response=self.client.get('/policies/');self.assertEqual(len(response.context['sections']),11)
        for slug,title in policies.SECTIONS:
            response=self.client.get('/policies/'+slug+'/');self.assertEqual(response.status_code,200)
            self.assertContains(response,'qa-v1');self.assertContains(response,'457/9 Điện Biên Phủ')
        for slug in ['warranty','loyalty']:self.assertEqual(self.client.get('/policies/'+slug+'/').status_code,200)
        for path in ['/','/contact/']:
            response=self.client.get(path);self.assertContains(response,'0824672384');self.assertContains(response,'maps.app.goo.gl/dhm5y4VkBiPHFYJY9')
        self.assertContains(self.client.get('/contact/'),'<iframe')

    def test_registration_terms_mandatory_and_marketing_optional(self):
        values=self.registration(accept_terms='');before=User.objects.count()
        response=self.client.post('/accounts/register/',values);self.assertEqual(response.status_code,200);self.assertEqual(User.objects.count(),before)
        values['accept_terms']='on';response=self.client.post('/accounts/register/',values);self.assertEqual(response.status_code,200)
        user=User.objects.get(username=values['username']);self.assertFalse(user.is_active)
        self.assertEqual(list(user.policy_events.filter(purpose='MARKETING').values_list('state',flat=True)),['DECLINED'])
        self.assertEqual(user.policy_events.filter(purpose='TERMS',state='ACCEPTED').count(),1)
        self.assertEqual(user.policy_events.filter(purpose='PRIVACY_NOTICE',state='PRESENTED').count(),1)
        self.client.post('/accounts/register/',values);self.assertEqual(User.objects.filter(username=values['username']).count(),1);self.assertEqual(user.policy_events.count(),3)

    def test_registration_rejects_forged_cross_session_and_ambiguous_consent(self):
        values=self.registration();values['policy_token']='forged';self.client.post('/accounts/register/',values)
        self.assertFalse(User.objects.filter(username=values['username']).exists())
        values=self.registration(accept_terms='off');self.client.post('/accounts/register/',values);self.assertFalse(User.objects.filter(username=values['username']).exists())
        values=self.registration();other=Client();other.post('/accounts/register/',values);self.assertFalse(User.objects.filter(username=values['username']).exists())

    def test_checkout_direct_post_terms_and_idempotent_evidence(self):
        from commerce.models import Order
        data=self.checkout_payload(accept_order_terms='');before=Order.objects.count()
        response=self.client.post('/checkout/',dict(data,action='place'));self.assertEqual(response.status_code,200);self.assertEqual(Order.objects.count(),before)
        data['accept_order_terms']='on'
        with patch('commerce.operations.scheduled_slot',return_value=timezone.now()+timezone.timedelta(hours=1)):
            response=self.client.post('/checkout/',dict(data,action='place'));self.assertEqual(response.status_code,302)
            order=Order.objects.latest('pk');self.assertEqual(order.total,28000);self.assertEqual(order.policy_events.count(),6)
            self.client.post('/checkout/',dict(data,action='place'));self.assertEqual(Order.objects.count(),before+1);self.assertEqual(order.policy_events.count(),6)
        self.assertTrue(all(e.content_hash==e.revision.content_hash for e in order.policy_events.select_related('revision')))
        self.assertFalse(ConsentEvent.objects.filter(purpose='MARKETING').exists())

    def test_checkout_wrong_purpose_expired_token_and_csrf_are_rejected(self):
        from commerce.models import Order
        data=self.checkout_payload();before=Order.objects.count()
        account_token=self.token('/account/privacy/')
        response=self.client.post('/checkout/',dict(data,policy_token=account_token,action='place'))
        self.assertEqual(response.status_code,200);self.assertEqual(Order.objects.count(),before)
        import time
        with patch('django.core.signing.time.time',return_value=time.time()+4000):
            response=self.client.post('/checkout/',dict(data,action='place'))
        self.assertEqual(response.status_code,200);self.assertEqual(Order.objects.count(),before)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user)
        self.assertEqual(csrf.post('/checkout/',dict(data,action='place')).status_code,403)

    def test_account_old_user_not_assumed_opted_and_withdrawal_is_append_only(self):
        self.client.force_login(self.user);self.assertFalse(ConsentEvent.objects.exists())
        page=self.client.get('/account/privacy/');html=page.content.decode()
        self.assertEqual(html.count('>Quyền riêng tư</a>'),1)
        self.assertContains(page,'Quản lý quyền riêng tư')
        self.assertContains(page,'Nhận thông tin ưu đãi qua email')
        self.assertContains(page,'Cho phép thống kê truy cập')
        self.assertNotContains(page,'SHA256:')
        token=self.token('/account/privacy/');self.assertFalse(ConsentEvent.objects.exists())
        response=self.client.post('/account/privacy/',{'policy_token':token,'marketing':'on','analytics':'on'});self.assertEqual(response.status_code,302)
        self.assertTrue(policies.preference(self.user,'MARKETING'));self.assertTrue(policies.preference(self.user,'ANALYTICS'))
        token=self.token('/account/privacy/');self.client.post('/account/privacy/',{'policy_token':token})
        self.assertFalse(policies.preference(self.user,'MARKETING'));self.assertEqual(ConsentEvent.objects.filter(state='WITHDRAWN').count(),2)
        self.assertEqual(ConsentEvent.objects.filter(state='ACCEPTED').count(),2)
        self.client.post('/account/privacy/',{'policy_token':token});self.assertEqual(ConsentEvent.objects.count(),4)

    def test_new_version_invalidates_old_token_and_optional_consent(self):
        values=self.registration();policy=Policy.objects.get(slug='terms');old=policy.revisions.get(status='PUBLISHED');original_body=old.body;original_hash=old.content_hash
        newer=PolicyRevision.objects.create(policy=policy,version='qa-v2',title=old.title,body='Updated terms',effective_at=timezone.now()-timezone.timedelta(seconds=1),reviewed=True,review_note='QA only',created_by=self.admin)
        policies.publish(self.admin,newer.pk);response=self.client.post('/accounts/register/',values)
        self.assertEqual(response.status_code,200);self.assertFalse(User.objects.filter(username=values['username']).exists())
        old.refresh_from_db();self.assertEqual(old.status,'ARCHIVED');self.assertEqual(old.body,original_body);self.assertEqual(old.content_hash,original_hash)
        self.client.force_login(self.user);token=self.token('/account/privacy/');self.client.post('/account/privacy/',{'policy_token':token,'marketing':'on'})
        self.assertTrue(policies.preference(self.user,'MARKETING'))
        privacy=Policy.objects.get(slug='privacy');old_privacy=privacy.revisions.get(status='PUBLISHED')
        revision=PolicyRevision.objects.create(policy=privacy,version='qa-v2',title=old_privacy.title,body=old_privacy.body+'\nChanged notice',reviewed=True,review_note='QA only',effective_at=timezone.now(),created_by=self.admin)
        before=ConsentEvent.objects.count();policies.publish(self.admin,revision.pk)
        self.assertFalse(policies.preference(self.user,'MARKETING'));self.assertEqual(ConsentEvent.objects.count(),before)

    def test_admin_publish_requires_review_date_permissions_and_old_versions_immutable(self):
        policy=Policy.objects.get(slug='terms');draft=PolicyRevision.objects.create(policy=policy,version='draft-next',title='Next',body='Draft only',created_by=self.admin)
        with self.assertRaises(ValidationError):policies.publish(self.admin,draft.pk)
        with self.assertRaises(PermissionDenied):policies.publish(self.staff,draft.pk)
        self.client.force_login(self.admin);response=self.client.get(f'/admin/support/policy/{policy.pk}/change/');self.assertEqual(response.status_code,200);self.assertContains(response,'Lịch sử chấp thuận')
        old=policy.revisions.get(status='PUBLISHED');old.body='Tamper'
        with self.assertRaises(ValidationError):old.save()
        for user in [self.user,self.staff]:
            self.client.force_login(user);self.assertNotEqual(self.client.get(f'/admin/support/policy/{policy.pk}/versions/').status_code,200)
            self.assertNotEqual(self.client.get('/admin/support/consentevent/').status_code,200)

    def test_csrf_account_and_admin_preview_escapes_stored_xss(self):
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user)
        self.assertEqual(csrf.post('/account/privacy/',{'marketing':'on'}).status_code,403)
        policy=Policy.objects.get(slug='terms');self.client.force_login(self.admin)
        response=self.client.post(f'/admin/support/policy/{policy.pk}/versions/',{'action':'preview','version':'preview','title':'Safe','body':'<script>alert(1)</script>','review_note':''})
        self.assertEqual(response.status_code,200);self.assertNotContains(response,'<script>alert(1)</script>');self.assertContains(response,'&lt;script&gt;')

    def test_policy_rich_text_subset_is_consistent_and_rejects_dangerous_links(self):
        policy=Policy.objects.get(slug='terms');self.client.force_login(self.admin)
        body='## Tiêu đề **đậm**\n\n### Mục nhỏ\n\nĐoạn *nghiêng* với [liên kết](https://example.com/policy).\n\n- Một\n- Hai\n\n1. Trước\n2. Sau\n\n[xấu](javascript:alert(1)) <img src=x onerror=alert(2)>'
        response=self.client.post(f'/admin/support/policy/{policy.pk}/versions/',{
            'action':'preview','version':'rich-preview','title':'Rich preview','body':body,'review_note':''})
        self.assertEqual(response.status_code,200)
        for html in ['<h2>Tiêu đề <strong>đậm</strong></h2>','<h3>Mục nhỏ</h3>','<em>nghiêng</em>']:
            self.assertContains(response,html,html=True)
        self.assertContains(response,'href="https://example.com/policy"')
        self.assertContains(response,'<ul>');self.assertContains(response,'<ol>')
        self.assertNotContains(response,'href="javascript:')
        self.assertNotContains(response,'<img src=x')
        self.assertContains(response,'&lt;img src=x onerror=alert(2)&gt;')
        # Existing heading syntax remains rendered, without rewriting stored content.
        response=self.client.post(f'/admin/support/policy/{policy.pk}/versions/',{
            'action':'preview','version':'legacy-preview','title':'Legacy','body':'**Tiêu đề cũ**\n\nVăn bản thuần.','review_note':''})
        self.assertContains(response,'<h2>Tiêu đề cũ</h2>',html=True)

    def test_publication_unavailable_fails_closed(self):
        PolicyRevision.objects.filter(policy__slug='terms',status='PUBLISHED').update(status='ARCHIVED')
        values={'full_name':'Khách mới','phone':'0901234578','email':'new@example.invalid','username':'not-created','password1':PASSWORD,'password2':PASSWORD,'accept_terms':'on','policy_token':'forged'}
        self.assertEqual(self.client.post('/accounts/register/',values).status_code,200);self.assertFalse(User.objects.filter(username='not-created').exists())
        self.assertEqual(self.client.get('/policies/terms/').status_code,404)

    def test_admin_audit_read_only_requires_specific_permission(self):
        self.client.post('/accounts/register/',self.registration())
        event=ConsentEvent.objects.first();before=ConsentEvent.objects.count()
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/admin/support/consentevent/').status_code,200)
        self.assertEqual(self.client.get(f'/admin/support/consentevent/{event.pk}/change/').status_code,200)
        self.assertEqual(self.client.post(f'/admin/support/consentevent/{event.pk}/change/',{'state':'WITHDRAWN'}).status_code,403)
        self.assertEqual(self.client.post(f'/admin/support/consentevent/{event.pk}/delete/').status_code,403)
        self.admin.user_permissions.remove(Permission.objects.get(codename='view_consentevent'))
        self.assertEqual(self.client.get('/admin/support/consentevent/').status_code,403)
        self.assertEqual(ConsentEvent.objects.count(),before)

    def test_consent_evidence_and_policy_hash_db_guards(self):
        self.client.post('/accounts/register/',self.registration());event=ConsentEvent.objects.first()
        with self.assertRaises(ValidationError):event.delete()
        if connection.vendor=='postgresql':
            with self.assertRaises(DatabaseError),transaction.atomic():ConsentEvent.objects.filter(pk=event.pk).update(state='WITHDRAWN')
            with self.assertRaises(DatabaseError),transaction.atomic():PolicyRevision.objects.filter(pk=event.revision_id).update(body='Tamper')
        self.assertNotIn('ip',[f.name for f in ConsentEvent._meta.fields])
        self.assertNotIn('token',[f.name for f in ConsentEvent._meta.fields])

    @override_settings(NAU_TRAFFIC_ENABLED=True)
    def test_nonessential_analytics_off_until_customer_opts_in(self):
        self.client.force_login(self.user)
        with patch('catalog.traffic.append') as append:
            self.client.get('/menu/',HTTP_USER_AGENT='Mozilla/5.0');append.assert_not_called()
            token=self.token('/account/privacy/');self.client.post('/account/privacy/',{'policy_token':token,'analytics':'on'})
            self.client.get('/menu/',HTTP_USER_AGENT='Mozilla/5.0');self.assertEqual(append.call_count,1)
            token=self.token('/account/privacy/');self.client.post('/account/privacy/',{'policy_token':token})
            self.client.get('/menu/',HTTP_USER_AGENT='Mozilla/5.0');self.assertEqual(append.call_count,1)

# Real PostgreSQL locks, not SQLite simulation.
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace
from unittest import skipUnless
from django.test import TransactionTestCase
from django.db import close_old_connections,connections
from django.http import QueryDict

@skipUnless(connection.vendor=='postgresql','PostgreSQL required')
@override_settings(**FLAGS)
class PolicyConcurrencyTests(TransactionTestCase):
    def setUp(self):published_fixture(type(self))
    def race(self,functions):
        barrier=Barrier(2)
        def run(fn):
            close_old_connections()
            try:barrier.wait(timeout=10);return fn()
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:return list(pool.map(run,functions))
    def test_conflicting_preference_replay_cannot_partially_overwrite_choices(self):
        req=SimpleNamespace(user=self.user,session={},POST=QueryDict(''))
        token=policies.issue_token(req,'account')
        def change(chosen):
            request=SimpleNamespace(user=User.objects.get(pk=self.user.pk),session=dict(req.session),POST=QueryDict(''))
            try:policies.update_preferences(request,token,chosen,chosen);return 'saved'
            except ValidationError:return 'replay'
        self.assertCountEqual(self.race([lambda:change(True),lambda:change(False)]),['saved','replay'])
        self.assertEqual(ConsentEvent.objects.count(),2)
        self.assertEqual(policies.preference(self.user,'MARKETING'),policies.preference(self.user,'ANALYTICS'))
    def test_competing_publications_keep_versions_and_one_current_document(self):
        policy=Policy.objects.get(slug='terms')
        revisions=[PolicyRevision.objects.create(policy=policy,version=f'qa-next-{i}',title='Next',body='QA draft',reviewed=True,review_note='QA only',effective_at=timezone.now(),created_by=self.admin) for i in range(2)]
        def publish(r):policies.publish(User.objects.get(pk=self.admin.pk),r.pk);return 'published'
        self.assertEqual(self.race([lambda:publish(revisions[0]),lambda:publish(revisions[1])]),['published','published'])
        self.assertEqual(policy.revisions.filter(status='PUBLISHED').count(),1);self.assertEqual(policy.revisions.count(),3)
