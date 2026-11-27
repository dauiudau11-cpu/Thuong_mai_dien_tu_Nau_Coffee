"""Gmail setup and multipart account emails, no external SMTP connection permitted."""
import os
import smtplib
import socket
import tempfile
from pathlib import Path
from unittest.mock import patch
from django.test import TestCase,SimpleTestCase,override_settings
from django.core import mail
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone
from datetime import timedelta
from config.email_settings import email_configuration
from catalog import customer_accounts as accounts
from tests import test_customer_accounts as phase1


class GmailConfigurationTests(SimpleTestCase):
    def test_selected_provider_defaults_and_no_password_default(self):
        cfg=email_configuration({})
        self.assertEqual(cfg['EMAIL_HOST'],'smtp.gmail.com');self.assertEqual(cfg['EMAIL_PORT'],587)
        self.assertTrue(cfg['EMAIL_USE_TLS']);self.assertFalse(cfg['EMAIL_USE_SSL'])
        self.assertEqual(cfg['EMAIL_TIMEOUT'],15)
        self.assertEqual(cfg['EMAIL_HOST_USER'],'naucoffee.official@gmail.com')
        self.assertEqual(cfg['DEFAULT_FROM_EMAIL'],'Nâu Coffee <naucoffee.official@gmail.com>')
        self.assertEqual(cfg['EMAIL_HOST_PASSWORD'],'');self.assertFalse(cfg['NAU_ACCOUNT_EMAIL_READY'])
        self.assertEqual(cfg['EMAIL_BACKEND'],'django.core.mail.backends.smtp.EmailBackend')

    def test_private_file_whitelist_permissions_and_environment_precedence(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'smtp.env';p.write_text('DJANGO_EMAIL_HOST_PASSWORD=fictional-only\n');p.chmod(0o600)
            cfg=email_configuration({'NAU_SMTP_ENV_FILE':str(p)})
            self.assertEqual(cfg['EMAIL_HOST_PASSWORD'],'fictional-only')
            cfg=email_configuration({'NAU_SMTP_ENV_FILE':str(p),'DJANGO_EMAIL_HOST_PASSWORD':'environment-fixture'})
            self.assertEqual(cfg['EMAIL_HOST_PASSWORD'],'environment-fixture')
            p.chmod(0o644)
            with self.assertRaises(ImproperlyConfigured):email_configuration({'NAU_SMTP_ENV_FILE':str(p)})
            p.chmod(0o600);p.write_text('DATABASE_URL=should-never-load\n')
            with self.assertRaises(ImproperlyConfigured):email_configuration({'NAU_SMTP_ENV_FILE':str(p)})
            p.write_text('DJANGO_EMAIL_HOST_PASSWORD=${SECRET_MUST_NOT_INTERPOLATE}\n')
            self.assertEqual(email_configuration({'NAU_SMTP_ENV_FILE':str(p)})['EMAIL_HOST_PASSWORD'],'${SECRET_MUST_NOT_INTERPOLATE}')
            link=Path(directory)/'link';link.symlink_to(p)
            with self.assertRaises(ImproperlyConfigured):email_configuration({'NAU_SMTP_ENV_FILE':str(link)})

    def test_bad_settings_fail_without_secret_or_console_fallback(self):
        for env in ({'DJANGO_EMAIL_PORT':'bad-sensitive-value'}, {'DJANGO_EMAIL_TIMEOUT':'0'},
                    {'DJANGO_EMAIL_USE_TLS':'maybe-secret'}, {'DJANGO_EMAIL_USE_SSL':'True'}):
            with self.assertRaises(ImproperlyConfigured) as error:email_configuration(env)
            self.assertNotIn('sensitive',str(error.exception));self.assertNotIn('maybe-secret',str(error.exception))

    def test_django_smtp_opens_starttls_with_selected_identity_and_timeout(self):
        from django.core.mail import get_connection
        cfg=email_configuration({'DJANGO_EMAIL_HOST_PASSWORD':'a'*16})
        with override_settings(**cfg),patch('smtplib.SMTP') as smtp:
            backend=get_connection(fail_silently=False)
            self.assertTrue(backend.open())
            smtp.assert_called_once_with('smtp.gmail.com',587,local_hostname=smtp.call_args.kwargs['local_hostname'],timeout=15)
            smtp.return_value.starttls.assert_called_once()
            smtp.return_value.login.assert_called_once_with('naucoffee.official@gmail.com','a'*16)
            backend.close()


@override_settings(**phase1.EMAIL_SETTINGS)
class GmailEmailTests(TestCase):
    @classmethod
    def setUpTestData(cls):phase1.CustomerAccountTests.setUpTestData.__func__(cls)
    data=phase1.CustomerAccountTests.data
    make=phase1.CustomerAccountTests.make

    def test_plain_and_branded_html_with_staff_invitation(self):
        profile=self.make();self.assertEqual(accounts.send_activation(profile.user_id),'sent')
        message=mail.outbox[-1]
        self.assertIn(profile.user.username,message.body)
        self.assertIn('24 giờ',message.body);self.assertNotIn(phase1.PASSWORD,message.body)
        self.assertEqual(message.alternatives[0].mimetype,'text/html')
        html=message.alternatives[0].content
        self.assertIn('NÂU COFFEE',html);self.assertIn('Hỗ trợ khách hàng',html)
        self.assertIn('#697448',html);self.assertIn('max-width:600px',html)
        self.assertIn('/accounts/activate/#token=',html)
        self.assertNotIn(profile.phone,html)
        other=accounts.create_customer(dict(full_name='Khách Thư Mời',phone='0901234568',email='invite@example.invalid'),actor=self.staff)
        self.assertEqual(accounts.send_activation(other.user_id),'sent')
        self.assertIn('mời thiết lập',mail.outbox[-1].subject)
        self.assertIn('tự đặt mật khẩu',mail.outbox[-1].body.lower())
        self.assertFalse(other.user.has_usable_password())

    def test_authentication_disconnect_and_timeout_are_not_silent_success(self):
        profile=self.make()
        for error in (smtplib.SMTPAuthenticationError(535,b'Simulated failure'),
                      smtplib.SMTPServerDisconnected('Simulated disconnect'),socket.timeout('Simulated timeout')):
            profile.last_email_attempt=None;profile.save(update_fields=['last_email_attempt'])
            with patch('catalog.customer_accounts.EmailMultiAlternatives.send',side_effect=error):
                self.assertEqual(accounts.send_activation(profile.user_id),'failed')
            profile.user.refresh_from_db();self.assertFalse(profile.user.is_active)
            self.assertFalse(mail.outbox)

    def test_live_gate_rejects_missing_credentials_localhost_and_malicious_origin(self):
        defaults=dict(NAU_ACCOUNT_ALLOW_TEST_EMAIL=False,NAU_ACCOUNT_EMAIL_READY=True,
            EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',EMAIL_HOST='smtp.gmail.com',
            EMAIL_HOST_USER='naucoffee.official@gmail.com',EMAIL_HOST_PASSWORD='a'*16,
            EMAIL_PORT=587,EMAIL_USE_TLS=True,EMAIL_USE_SSL=False,EMAIL_TIMEOUT=15,
            DEFAULT_FROM_EMAIL='Nâu Coffee <naucoffee.official@gmail.com>',NAU_ACCOUNT_PUBLIC_ORIGIN='https://coffee.example.org')
        with override_settings(**defaults):
            self.assertTrue(accounts.email_ready())
            for origin in ('http://coffee.example.org','http://localhost:8000','https://127.0.0.1',
                           'https://localhost','https://coffee.invalid','https://user:secret@coffee.example.org',
                           'https://coffee.example.org/path','https://coffee.example.org?x=1'):
                with override_settings(NAU_ACCOUNT_PUBLIC_ORIGIN=origin):self.assertFalse(accounts.email_ready())
            for changes in ({'EMAIL_HOST_PASSWORD':''},{'EMAIL_USE_TLS':False},{'EMAIL_HOST_USER':'other@example.invalid'},
                            {'EMAIL_BACKEND':'django.core.mail.backends.console.EmailBackend'}):
                with override_settings(**changes):self.assertFalse(accounts.email_ready())

    def test_resend_and_repeated_staff_submission_do_not_duplicate_mail_or_accounts(self):
        profile=self.make();self.assertEqual(accounts.send_activation(profile.user_id),'sent')
        self.assertEqual(accounts.send_activation(profile.user_id),'throttled');self.assertEqual(len(mail.outbox),1)
        self.client.force_login(self.staff)
        data={'full_name':'Khách SMTP','phone':'0901234568','email':'once@example.invalid'}
        self.client.post('/dashboard/customers/create/',data);before=len(mail.outbox)
        self.client.post('/dashboard/customers/create/',data)
        self.assertEqual(len(mail.outbox),before)


from unittest import skipUnless
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from django.db import connection, connections
from django.test import TransactionTestCase


@skipUnless(connection.vendor=='postgresql','Requires independently attested PostgreSQL QA')
@override_settings(**phase1.EMAIL_SETTINGS)
class GmailEmailConcurrencyTests(TransactionTestCase):
    def test_double_submit_sends_only_one_email(self):
        profile=accounts.create_customer(dict(full_name='Khách Gửi Thư',phone='0901234567',
            email='concurrent@example.invalid',username='smtp-concurrent',password1=phase1.PASSWORD))
        barrier=Barrier(2);sent=[];lock=Lock()
        def accept(*args,**kwargs):
            with lock:sent.append('accepted')
            return 1
        def submit(index):
            try:barrier.wait(timeout=10);return accounts.send_activation(profile.user_id)
            finally:connections.close_all()
        with patch('catalog.customer_accounts.EmailMultiAlternatives.send',side_effect=accept),ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(submit,range(2)))
        self.assertCountEqual(results,['sent','throttled']);self.assertEqual(len(sent),1)
