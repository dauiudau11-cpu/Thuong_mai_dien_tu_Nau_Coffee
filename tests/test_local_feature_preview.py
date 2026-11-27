"""Local cutover guard and SMTP capture; no database use or real mail."""
import json
import os
from pathlib import Path
import smtplib
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import SimpleTestCase,RequestFactory,override_settings
from config import local_preview as local


@override_settings(ALLOWED_HOSTS=['127.0.0.1','localhost'])
class LocalPreviewTests(SimpleTestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.out=self.root/'outbox';self.out.mkdir(mode=0o700)
        self.profile={'mode':'closed','features_enabled':False,'smtp_port':25251,'smoke_key':'a'*64}
        self.file=self.root/'runtime.json';self.file.write_text(json.dumps(self.profile));self.file.chmod(0o600)
        self.patch=patch.multiple(local,RUNTIME=self.root,PROFILE=self.file,OUTBOX=self.out);self.patch.start();self.addCleanup(self.patch.stop)
        self.rf=RequestFactory()

    def request(self,**meta):
        return self.rf.get('/',HTTP_HOST='127.0.0.1:8000',REMOTE_ADDR=meta.pop('REMOTE_ADDR','127.0.0.1'),**meta)

    def test_exact_target_and_rejects_qa_dev_admin_ports(self):
        good=dict(ENGINE='django.db.backends.postgresql',NAME='nau_coffee_test',USER='nau_coffee_test_runner',HOST='127.0.0.1',PORT='5432')
        local.guard_config(good)
        for changes in ({'NAME':'nau_coffee_dev'},{'NAME':'nau_coffee_qa_accounts'},{'USER':'postgres'},{'PORT':'55441'},{'HOST':'0.0.0.0'},{'ENGINE':'sqlite3'}):
            with self.assertRaises(ImproperlyConfigured):local.guard_config(good|changes)

    def test_profile_must_be_private_owned_regular(self):
        self.assertEqual(local.read_profile()['mode'],'closed')
        self.file.chmod(0o644)
        with self.assertRaises(ImproperlyConfigured):local.read_profile()
        self.file.chmod(0o600);self.file.unlink();self.file.symlink_to(self.root/'missing')
        with self.assertRaises(ImproperlyConfigured):local.read_profile()

    def test_invalid_profile_cannot_open_gate(self):
        self.profile['mode']='unknown';local.write_profile(self.profile)
        with self.assertRaises(ImproperlyConfigured):local.read_profile()

    def test_closed_gate_blocks_local_users(self):
        gate=local.LocalOnlyMiddleware(lambda r:HttpResponse('ok'))
        self.assertEqual(gate(self.request()).status_code,503)

    def test_smoke_cookie_only_during_maintenance(self):
        self.profile['mode']='smoke';local.write_profile(self.profile)
        gate=local.LocalOnlyMiddleware(lambda r:HttpResponse('ok'))
        self.assertEqual(gate(self.request()).status_code,503)
        req=self.request();req.COOKIES['nau_local_smoke']='a'*64
        self.assertEqual(gate(req).status_code,200)

    def test_external_remote_denied_even_with_cookie(self):
        self.profile['mode']='open';local.write_profile(self.profile)
        gate=local.LocalOnlyMiddleware(lambda r:HttpResponse('ok'))
        self.assertEqual(gate(self.request(REMOTE_ADDR='192.0.2.1')).status_code,403)

    def test_missing_profile_fails_closed(self):
        self.file.unlink();gate=local.LocalOnlyMiddleware(lambda r:HttpResponse('ok'))
        self.assertEqual(gate(self.request()).status_code,503)

    def test_sandbox_stores_exactly_one_message_private_no_relay(self):
        sink=local.SandboxSMTP();sink.start()
        try:
            with smtplib.SMTP('127.0.0.1',25251,timeout=5) as smtp:
                smtp.sendmail('from@example.invalid',['to@example.invalid'],'Subject: Local capture\r\n\r\nSandbox only')
            files=list(self.out.glob('*.eml'));self.assertEqual(len(files),1)
            self.assertEqual(files[0].stat().st_mode&0o777,0o600)
            self.assertIn(b'Sandbox only',files[0].read_bytes())
        finally:sink.stop()

    def test_mailbox_requires_admin_and_does_not_expose_mail_to_staff(self):
        request=self.request();request.user=SimpleNamespace(is_authenticated=False)
        self.assertEqual(local.mailbox(request).status_code,302)
        request.user=SimpleNamespace(is_authenticated=True)
        with patch('catalog.permissions.has_role',return_value=False):
            self.assertEqual(local.mailbox(request).status_code,403)

    def test_non_ascii_or_malformed_smoke_cookie_cannot_raise_or_open_gate(self):
        self.profile['mode']='smoke';local.write_profile(self.profile)
        gate=local.LocalOnlyMiddleware(lambda r:HttpResponse('ok'))
        for cookie in ('é','a'*1000,'not-a-key'):
            req=self.request();req.COOKIES['nau_local_smoke']=cookie
            self.assertEqual(gate(req).status_code,503)
