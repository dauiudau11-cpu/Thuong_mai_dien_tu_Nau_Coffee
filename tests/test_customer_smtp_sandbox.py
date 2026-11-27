"""Django's real SMTP backend against a loopback in-memory sink, never a customer mailbox."""
from contextlib import contextmanager
from email import policy
from email.parser import BytesParser
import re
import socketserver
import threading
from django.test import TestCase, override_settings
from django.core.exceptions import ValidationError
from catalog import customer_accounts as accounts
from tests import test_customer_accounts as phase1


class SMTPHandler(socketserver.StreamRequestHandler):
    def send(self, value):
        self.wfile.write(value);self.wfile.flush()

    def handle(self):
        self.send(b'220 sandbox.invalid SMTP\r\n')
        while True:
            line=self.rfile.readline(65536)
            if not line:return
            command=line.split(b' ',1)[0].strip().upper()
            if command in (b'EHLO',b'HELO'):
                self.send(b'250-sandbox.invalid\r\n250 SIZE 65536\r\n')
            elif command==b'MAIL':self.send(b'250 OK\r\n')
            elif command==b'RCPT':
                # Only generated .invalid recipients can enter this sandbox.
                if b'@example.invalid>' not in line.lower():
                    self.send(b'550 Only synthetic recipients permitted\r\n')
                else:self.send(b'550 Simulated rejection\r\n' if self.server.reject else b'250 OK\r\n')
            elif command==b'DATA':
                self.send(b'354 End with dot\r\n');rows=[]
                while True:
                    row=self.rfile.readline(65536)
                    if not row:return
                    if row==b'.\r\n':break
                    rows.append(row[1:] if row.startswith(b'..') else row)
                self.server.messages.append(b''.join(rows))
                self.send(b'250 Accepted by local sandbox\r\n')
            elif command==b'QUIT':self.send(b'221 Bye\r\n');return
            elif command in (b'RSET',b'NOOP'):self.send(b'250 OK\r\n')
            else:self.send(b'502 Not implemented\r\n')


@contextmanager
def smtp_sink(*, reject=False):
    with socketserver.ThreadingTCPServer(('127.0.0.1',0),SMTPHandler) as server:
        server.daemon_threads=True;server.messages=[];server.reject=reject
        thread=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.05},daemon=True)
        thread.start()
        try:yield server
        finally:server.shutdown();thread.join(timeout=2)


@override_settings(**phase1.EMAIL_SETTINGS)
class CustomerSMTPSandboxTests(TestCase):
    def make(self):
        return accounts.create_customer(dict(full_name='Khách SMTP giả lập',phone='0901234567',
            email='sandbox@example.invalid',username='smtp-synthetic',password1=phase1.PASSWORD))

    def test_real_smtp_protocol_send_resend_and_activate_without_external_mail(self):
        profile=self.make()
        with smtp_sink() as server, override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
                EMAIL_HOST='127.0.0.1',EMAIL_PORT=server.server_address[1],EMAIL_HOST_USER='',EMAIL_HOST_PASSWORD='',
                EMAIL_USE_TLS=False,EMAIL_USE_SSL=False):
            self.assertEqual(accounts.send_activation(profile.user_id),'sent')
            self.assertEqual(len(server.messages),1)
            message=BytesParser(policy=policy.default).parsebytes(server.messages[0])
            self.assertEqual(message['To'],'sandbox@example.invalid')
            body=message.get_body(preferencelist=('plain',)).get_content();self.assertIn('smtp-synthetic',body)
            old=re.search(r'#token=(\S+)',body)[1]
            self.assertEqual(accounts.send_activation(profile.user_id),'throttled')
            self.assertEqual(len(server.messages),1)
            profile.last_email_attempt=None;profile.save(update_fields=['last_email_attempt'])
            self.assertEqual(accounts.send_activation(profile.user_id),'sent')
            self.assertEqual(len(server.messages),2)
            with self.assertRaises(ValidationError):accounts.activate(old,phase1.PASSWORD,phase1.PASSWORD)
            body=BytesParser(policy=policy.default).parsebytes(server.messages[-1]).get_body(preferencelist=('plain',)).get_content()
            token=re.search(r'#token=(\S+)',body)[1]
            accounts.activate(token,phase1.PASSWORD,phase1.PASSWORD)
            profile.user.refresh_from_db();self.assertTrue(profile.user.is_active)
            self.assertTrue(profile.user.check_password(phase1.PASSWORD))
            with self.assertRaises(ValidationError):accounts.activate(token,phase1.PASSWORD,phase1.PASSWORD)
        # No server.messages/body/token are persisted or printed.

    def test_smtp_rejection_preserves_pending_account_and_reports_failed(self):
        profile=self.make()
        with smtp_sink(reject=True) as server, override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
                EMAIL_HOST='127.0.0.1',EMAIL_PORT=server.server_address[1],EMAIL_HOST_USER='',EMAIL_HOST_PASSWORD='',
                EMAIL_USE_TLS=False,EMAIL_USE_SSL=False):
            self.assertEqual(accounts.send_activation(profile.user_id),'failed')
            self.assertEqual(server.messages,[])
        profile.user.refresh_from_db();self.assertFalse(profile.user.is_active)
        self.assertIsNone(profile.email_verified_at)
