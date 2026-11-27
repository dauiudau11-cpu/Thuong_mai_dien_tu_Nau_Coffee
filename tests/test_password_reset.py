"""Customer recovery: generic public responses, standard tokens and locked writes."""
import io
import logging
import re
import smtplib
import socket
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch
from urllib.parse import urlsplit,parse_qs
from django.contrib.auth import authenticate
from django.contrib.auth.models import User,Group
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.db import connection,connections
from django.test import TestCase,TransactionTestCase,Client,override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from catalog import password_reset as reset
from catalog import customer_accounts as accounts
from catalog.customer_models import CustomerProfile
from support.models import SubmissionLimit
from tests import test_customer_accounts as phase1

REQUEST='/accounts/password/reset/'
EXCHANGE=REQUEST+'confirm/'
CONFIRM=REQUEST+'new/'
DONE=REQUEST+'done/'
COMPLETE=REQUEST+'complete/'
NEW='New-customer-safe-924!'
SETTINGS=dict(phase1.EMAIL_SETTINGS,PASSWORD_RESET_TIMEOUT=3600,
    DEFAULT_FROM_EMAIL='Nâu Coffee <naucoffee.official@gmail.com>')


class Helpers:
    data=phase1.CustomerAccountTests.data
    make=phase1.CustomerAccountTests.make

    def link(self,user=None):
        user=user or self.profile.user
        return dict(uid=urlsafe_base64_encode(force_bytes(user.pk)),token=default_token_generator.make_token(user))

    def exchange(self,client=None,link=None):
        return (client or self.client).post(EXCHANGE,link or self.link())

    def password(self,client=None,password=NEW):
        client=client or self.client
        return client.post(CONFIRM,dict(new_password1=password,new_password2=password,reset_uid=client.session.get(reset.UID_KEY,'')))


def fixture(cls):
    phase1.CustomerAccountTests.setUpTestData.__func__(cls)
    cls.staff.email='staff-only@example.invalid';cls.staff.save(update_fields=['email'])
    cls.profile=accounts.create_customer(phase1.CustomerAccountTests.data(cls))
    accounts.activate(accounts.token_for(cls.profile),phase1.PASSWORD,phase1.PASSWORD)
    cls.profile.refresh_from_db()


@override_settings(**SETTINGS)
class CustomerPasswordResetTests(Helpers,TestCase):
    @classmethod
    def setUpTestData(cls):fixture(cls)

    def test_feature_off_hides_every_route_and_login_link(self):
        with override_settings(NAU_CUSTOMER_ACCOUNTS_ENABLED=False):
            with patch('catalog.password_reset.EmailMultiAlternatives.send') as send:
                self.assertEqual(reset.send_recovery(self.profile.email),'unavailable')
                send.assert_not_called()
            for path in (REQUEST,EXCHANGE,CONFIRM,DONE,COMPLETE):self.assertEqual(self.client.get(path).status_code,404)
            self.assertNotContains(self.client.get('/accounts/login/'),'Quên mật khẩu?')

    def test_request_multipart_trusted_origin_and_no_password_or_host_injection(self):
        self.assertContains(self.client.get('/accounts/login/'),'Quên mật khẩu?')
        with override_settings(ALLOWED_HOSTS=['testserver','forged.example.invalid']):
            response=self.client.post(REQUEST,{'email':self.profile.email.upper()},HTTP_HOST='forged.example.invalid')
        self.assertRedirects(response,DONE,fetch_redirect_response=False);self.assertEqual(len(mail.outbox),1)
        message=mail.outbox[0]
        self.assertEqual(message.from_email,'Nâu Coffee <naucoffee.official@gmail.com>')
        self.assertEqual(message.to,[self.profile.email]);self.assertNotIn(phase1.PASSWORD,message.body)
        self.assertNotIn(self.profile.phone,message.body);self.assertNotIn('forged',message.body)
        self.assertIn('60 phút',message.body);self.assertEqual(message.alternatives[0].mimetype,'text/html')
        url=re.search(r'https://\S+',message.body)[0];parts=urlsplit(url)
        self.assertEqual(parts.netloc,'coffee.example.invalid');self.assertEqual(parts.path,EXCHANGE);self.assertEqual(parts.query,'')
        values={k:v[0] for k,v in parse_qs(parts.fragment).items()}
        self.assertTrue(default_token_generator.check_token(self.profile.user,values['token']))
        self.assertNotContains(self.client.get(DONE),values['token'])

    def test_unknown_pending_staff_admin_and_failure_same_public_response(self):
        emails=['unknown@example.invalid',self.profile.email,self.staff.email or 'staff@example.invalid']
        pending=accounts.create_customer(dict(full_name='Khách Chờ',phone='0901234568',email='pending@example.invalid'),actor=self.staff)
        emails.append(pending.email)
        admin=User.objects.create_superuser('reset-admin','admin@example.invalid',phase1.PASSWORD);emails.append(admin.email)
        reference=None
        for index,email in enumerate(emails):
            client=Client()
            with patch('catalog.password_reset.EmailMultiAlternatives.send',side_effect=smtplib.SMTPException('fixture failure')):
                response=client.post(REQUEST,{'email':email},REMOTE_ADDR=f'127.0.0.{index+1}',follow=True)
            self.assertEqual(response.status_code,200);self.assertEqual(response.redirect_chain,[(DONE,302)])
            if reference is None:reference=response.content
            self.assertEqual(response.content,reference)
        self.assertFalse(mail.outbox)

    def test_pending_staff_account_cannot_use_standard_token_to_bypass_activation(self):
        pending=accounts.create_customer(dict(full_name='Khách Chờ',phone='0901234568',email='pending@example.invalid'),actor=self.staff)
        self.assertEqual(self.exchange(link=self.link(pending.user)).status_code,200)
        pending.user.is_active=True;pending.user.set_password(phase1.PASSWORD);pending.user.save()
        self.assertEqual(self.exchange(link=self.link(pending.user)).status_code,200)
        self.assertNotIn(reset.TOKEN_KEY,self.client.session)
        self.assertIsNone(CustomerProfile.objects.get(pk=pending.pk).email_verified_at)

    def test_staff_admin_flags_and_groups_rejected_even_with_valid_django_token(self):
        for flag in ('is_staff','is_superuser'):
            user=User.objects.get(pk=self.profile.user_id);setattr(user,flag,True);user.save()
            self.assertEqual(self.exchange(link=self.link(user)).status_code,200)
            setattr(user,flag,False);user.save()
        for name in ('STAFF','ADMIN'):
            group=Group.objects.get_or_create(name=name)[0];self.profile.user.groups.add(group)
            self.assertEqual(self.exchange(link=self.link()).status_code,200)
            self.profile.user.groups.remove(group)
        self.assertNotIn(reset.TOKEN_KEY,self.client.session)

    def test_expired_token_both_at_exchange_and_at_password_write(self):
        user=self.profile.user;now=default_token_generator._now()
        with patch.object(default_token_generator,'_now',return_value=now):link=self.link(user)
        with patch.object(default_token_generator,'_now',return_value=now+timedelta(seconds=3601)):
            self.assertContains(self.exchange(link=link),'Liên kết không còn hợp lệ')
        with patch.object(default_token_generator,'_now',return_value=now):self.assertRedirects(self.exchange(link=link),CONFIRM)
        with patch.object(default_token_generator,'_now',return_value=now+timedelta(seconds=3601)):
            self.assertContains(self.password(),'Liên kết không còn hợp lệ')
        user.refresh_from_db();self.assertTrue(user.check_password(phase1.PASSWORD))

    def test_bad_token_uid_and_activation_token_fail_closed(self):
        for link in ({'uid':'bad','token':'bad'},{'uid':'x'*1000,'token':'x'*1000},
                     dict(self.link(),token='invalid'),dict(self.link(),token=accounts.token_for(self.profile))):
            self.assertContains(self.exchange(link=link),'Liên kết không còn hợp lệ')
            self.assertNotIn(reset.TOKEN_KEY,self.client.session)
        self.assertContains(self.client.get(CONFIRM),'Liên kết không còn hợp lệ')

    def test_success_hashes_password_invalidates_token_and_requires_login(self):
        link=self.link();oldsession=self.client.session.session_key
        response=self.exchange(link=link);self.assertRedirects(response,CONFIRM)
        self.assertNotEqual(oldsession,self.client.session.session_key)
        self.assertNotIn(link['token'],response['Location'])
        response=self.password();self.assertRedirects(response,COMPLETE)
        user=User.objects.get(pk=self.profile.user_id)
        self.assertNotEqual(user.password,NEW);self.assertTrue(user.check_password(NEW))
        self.assertIsNone(authenticate(username=user.username,password=phase1.PASSWORD))
        self.assertEqual(authenticate(username=user.username,password=NEW).pk,user.pk)
        self.assertFalse(default_token_generator.check_token(user,link['token']))
        self.assertNotIn(reset.TOKEN_KEY,self.client.session);self.assertNotIn('_auth_user_id',self.client.session)
        self.assertContains(self.exchange(link=link),'Liên kết không còn hợp lệ')

    def test_weak_mismatched_passwords_preserve_original_then_allow_retry(self):
        self.exchange()
        for first,second in [('123','123'),(NEW,'different')]:
            response=self.client.post(CONFIRM,{'new_password1':first,'new_password2':second,'reset_uid':self.client.session[reset.UID_KEY]})
            self.assertTrue(response.context['form'].errors)
            self.assertNotContains(response,'This password')
            if first=='123':self.assertContains(response,'Mật khẩu phải có ít nhất 8 ký tự.')
            user=User.objects.get(pk=self.profile.user_id);self.assertTrue(user.check_password(phase1.PASSWORD))
        self.assertRedirects(self.password(),COMPLETE)

    def test_csrf_required_at_request_exchange_and_final_password(self):
        client=Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(REQUEST,{'email':self.profile.email}).status_code,403)
        self.assertEqual(client.post(EXCHANGE,self.link()).status_code,403)
        client.get(EXCHANGE)
        data=dict(self.link(),csrfmiddlewaretoken=client.cookies['csrftoken'].value)
        self.assertEqual(client.post(EXCHANGE,data).status_code,302)
        self.assertEqual(client.post(CONFIRM,{'new_password1':NEW,'new_password2':NEW}).status_code,403)
        self.assertFalse(mail.outbox)

    def test_https_same_origin_csrf_works_and_foreign_origin_is_rejected(self):
        client=Client(enforce_csrf_checks=True)
        client.get(EXCHANGE,secure=True)
        csrf=client.cookies['csrftoken'].value
        data=dict(self.link(),csrfmiddlewaretoken=csrf)
        self.assertEqual(client.post(EXCHANGE,data,secure=True,HTTP_ORIGIN='https://foreign.example.invalid').status_code,403)
        self.assertEqual(client.post(EXCHANGE,data,secure=True,HTTP_REFERER='https://testserver'+EXCHANGE).status_code,302)
        response=client.post(CONFIRM,{'new_password1':NEW,'new_password2':NEW,'csrfmiddlewaretoken':csrf,'reset_uid':client.session[reset.UID_KEY]},
            secure=True,HTTP_REFERER='https://testserver'+CONFIRM)
        self.assertEqual(response.status_code,302)
        self.assertEqual(response['Location'],COMPLETE)

    def test_old_tab_cannot_reset_a_different_account_from_new_tab_session(self):
        self.exchange();first_uid=self.client.session[reset.UID_KEY]
        second=self.make(verified=True,username='second-recovery',phone='0901234568',email='second@example.invalid')
        self.exchange(link=self.link(second.user));second_uid=self.client.session[reset.UID_KEY]
        response=self.client.post(CONFIRM,dict(new_password1=NEW,new_password2=NEW,reset_uid=first_uid))
        self.assertContains(response,'Liên kết không còn hợp lệ')
        self.profile.user.refresh_from_db();second.user.refresh_from_db()
        self.assertTrue(self.profile.user.check_password(phase1.PASSWORD));self.assertTrue(second.user.check_password(phase1.PASSWORD))
        self.assertEqual(self.client.session[reset.UID_KEY],second_uid)
        self.assertRedirects(self.password(),COMPLETE)
        second.user.refresh_from_db();self.assertTrue(second.user.check_password(NEW))

    def test_per_email_and_ip_limits_do_not_reveal_identity_or_create_users(self):
        count=User.objects.count()
        first=self.client.post(REQUEST,{'email':self.profile.email},REMOTE_ADDR='127.0.0.2',follow=True)
        second=self.client.post(REQUEST,{'email':self.profile.email},REMOTE_ADDR='127.0.0.3',follow=True)
        self.assertEqual(first.content,second.content);self.assertEqual(len(mail.outbox),1)
        for index in range(7):self.client.post(REQUEST,{'email':f'unknown{index}@example.invalid'},REMOTE_ADDR='127.0.0.4')
        key='customer-reset-ip:'
        self.assertIn(5,SubmissionLimit.objects.filter(key__startswith=key).values_list('count',flat=True))
        self.assertEqual(User.objects.count(),count)

    def test_smtp_failures_leave_password_profile_and_account_unchanged(self):
        before=User.objects.values().get(pk=self.profile.user_id)
        profile_before=CustomerProfile.objects.values().get(pk=self.profile.pk)
        for error in (smtplib.SMTPAuthenticationError(535,b'fixture secret must not leak'),
                      smtplib.SMTPServerDisconnected('fixture disconnect'),socket.timeout('fixture timeout')):
            SubmissionLimit.objects.all().delete()
            with patch('catalog.password_reset.EmailMultiAlternatives.send',side_effect=error):
                self.assertEqual(reset.send_recovery(self.profile.email),'failed')
            self.assertEqual(User.objects.values().get(pk=self.profile.user_id),before)
            self.assertEqual(CustomerProfile.objects.values().get(pk=self.profile.pk),profile_before)
        self.assertFalse(mail.outbox)

    def test_unavailable_smtp_and_ambiguous_legacy_email_send_nothing(self):
        with override_settings(NAU_ACCOUNT_EMAIL_READY=False):self.assertEqual(reset.send_recovery(self.profile.email),'unavailable')
        SubmissionLimit.objects.all().delete()
        User.objects.create_user('ambiguous',email=' '+self.profile.email.upper()+' ')
        self.assertEqual(reset.send_recovery(self.profile.email),'ineligible');self.assertFalse(mail.outbox)

    def test_role_and_verification_rechecked_after_exchange(self):
        self.exchange();self.profile.user.groups.add(Group.objects.get_or_create(name='ADMIN')[0])
        self.assertContains(self.password(),'Liên kết không còn hợp lệ')
        self.profile.user.refresh_from_db();self.assertTrue(self.profile.user.check_password(phase1.PASSWORD))

    def test_revoked_verification_or_inactive_user_rechecked_before_write(self):
        self.exchange()
        CustomerProfile.objects.filter(pk=self.profile.pk).update(email_verified_at=None)
        self.assertContains(self.password(),'Liên kết không còn hợp lệ')
        from django.utils import timezone
        CustomerProfile.objects.filter(pk=self.profile.pk).update(email_verified_at=timezone.now())
        self.exchange()
        User.objects.filter(pk=self.profile.user_id).update(is_active=False)
        self.assertContains(self.password(),'Liên kết không còn hợp lệ')
        self.profile.user.refresh_from_db();self.assertTrue(self.profile.user.check_password(phase1.PASSWORD))

    def test_existing_sessions_invalidated_and_no_token_in_responses_or_logs(self):
        other=Client();other.force_login(self.profile.user);self.profile.user.refresh_from_db()
        link=self.link();stream=io.StringIO();handler=logging.StreamHandler(stream);logger=logging.getLogger();logger.addHandler(handler)
        try:
            response=self.exchange(link=link);page=self.client.get(CONFIRM)
            self.assertEqual(page['Referrer-Policy'],'same-origin');self.assertIn('no-store',page['Cache-Control'])
            self.assertNotIn(link['token'],page.content.decode());self.password()
        finally:logger.removeHandler(handler)
        self.assertNotIn(link['token'],stream.getvalue())
        self.assertEqual(other.get('/account/').status_code,302)

    def test_loopback_smtp_accepts_reset_multipart_without_external_email(self):
        from tests.test_customer_smtp_sandbox import smtp_sink
        from email import policy
        from email.parser import BytesParser
        with smtp_sink() as server,override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
                EMAIL_HOST='127.0.0.1',EMAIL_PORT=server.server_address[1],EMAIL_HOST_USER='',EMAIL_HOST_PASSWORD='',
                EMAIL_USE_TLS=False,EMAIL_USE_SSL=False):
            self.assertEqual(reset.send_recovery(self.profile.email),'sent')
            self.assertEqual(len(server.messages),1)
            message=BytesParser(policy=policy.default).parsebytes(server.messages[0])
            self.assertIn('naucoffee.official@gmail.com',str(message['From']))
            self.assertIn('#uid=',message.get_body(preferencelist=('plain',)).get_content())
            self.assertIn('Đặt mật khẩu mới',message.get_body(preferencelist=('html',)).get_content())

    def test_ip_limit_uses_direct_peer_even_with_login_and_spoofed_forwarded_header(self):
        self.client.force_login(self.profile.user)
        for index in range(7):
            self.client.post(REQUEST,{'email':f'no{index}@example.invalid'},REMOTE_ADDR='127.0.0.8',HTTP_X_FORWARDED_FOR=f'10.0.0.{index}')
        buckets=SubmissionLimit.objects.filter(key__startswith='customer-reset-ip:')
        self.assertEqual(buckets.count(),1);self.assertEqual(buckets.get().count,5)
        self.assertEqual(SubmissionLimit.objects.filter(key__startswith='customer-reset-email:').count(),5)


@skipUnless(connection.vendor=='postgresql','Independent PostgreSQL QA required')
@override_settings(**SETTINGS)
class PasswordResetConcurrencyTests(Helpers,TransactionTestCase):
    def setUp(self):fixture(self.__class__)

    def test_two_sessions_cannot_both_consume_the_same_token(self):
        link=self.link();clients=[Client(),Client()]
        for client in clients:self.assertEqual(self.exchange(client=client,link=link).status_code,302)
        barrier=Barrier(2)
        def submit(index):
            try:
                barrier.wait(timeout=10)
                return self.password(client=clients[index],password=f'New-Reset-Race-{index}-823!').status_code
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(submit,range(2)))
        self.assertCountEqual(results,[302,200]);user=User.objects.get(pk=self.profile.user_id)
        self.assertEqual(sum(user.check_password(f'New-Reset-Race-{i}-823!') for i in range(2)),1)
        self.assertFalse(default_token_generator.check_token(user,link['token']))

    def test_reset_email_double_submit_sends_only_one_message(self):
        barrier=Barrier(2)
        def request(index):
            try:barrier.wait(timeout=10);return reset.send_recovery(self.profile.email)
            finally:connections.close_all()
        with patch('catalog.password_reset.EmailMultiAlternatives.send',return_value=1) as send,ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(request,range(2)))
        self.assertCountEqual(results,['sent','throttled']);self.assertEqual(send.call_count,1)
