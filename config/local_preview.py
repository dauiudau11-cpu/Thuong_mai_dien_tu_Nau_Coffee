"""Fail-closed localhost operations. Never imported by the public URL configuration."""
import asyncio
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import threading
import uuid

from django.core.exceptions import ImproperlyConfigured, DisallowedHost

RUNTIME = Path.home() / '.local/share/nau-coffee/local-preview'
PROFILE = RUNTIME / 'runtime.json'
OUTBOX = RUNTIME / 'outbox'
EXPECTED = ('nau_coffee_test', 'nau_coffee_test_runner', '127.0.0.1', '5432')


def require_private(path, directory=False):
    expected_mode = 0o700 if directory else 0o600
    if (path.is_symlink() or not path.exists() or path.stat().st_uid != os.getuid()
            or path.stat().st_mode & 0o777 != expected_mode
            or (directory and not path.is_dir()) or (not directory and not path.is_file())):
        raise ImproperlyConfigured('Local runtime requires owned private files/directories.')


def read_profile():
    require_private(RUNTIME, True)
    require_private(PROFILE)
    value = json.loads(PROFILE.read_text())
    if (value.get('mode') not in ('closed', 'smoke', 'open', 'failed')
            or type(value.get('features_enabled')) is not bool
            or type(value.get('policy_enabled', False)) is not bool
            or not re.fullmatch(r'[a-f0-9]{64}', value.get('smoke_key', ''))
            or value.get('smtp_port') != 25251):
        raise ImproperlyConfigured('Invalid local runtime profile; refusing access.')
    return value


def write_profile(value):
    require_private(RUNTIME, True)
    temp = RUNTIME / ('.profile-' + secrets.token_hex(8))
    with os.fdopen(os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as f:
        json.dump(value, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(temp, PROFILE)


def guard_config(config):
    actual = (config.get('NAME'), config.get('USER'), config.get('HOST'), str(config.get('PORT')))
    if config.get('ENGINE') != 'django.db.backends.postgresql' or actual != EXPECTED:
        raise ImproperlyConfigured('Local maintenance permits only the approved preview identity at 5432.')


def verify_instance():
    from .test_runner import verify_qa_instance
    verify_qa_instance({'ENGINE': 'django.db.backends.postgresql', 'NAME': 'nau_coffee_qa_accounts',
        'USER': 'nau_coffee_qa_accounts_runner', 'HOST': '127.0.0.1', 'PORT': '55441',
        'TEST': {'NAME': 'nau_coffee_qa_accounts'}})
    try:
        result = subprocess.run(['docker', 'inspect', 'pg_lab_postgres', 'nau_localization_qa_20261111'],
            capture_output=True, check=True, timeout=10)
        preview, qa = json.loads(result.stdout)
        profile = read_profile()
        if (preview['Id'] != profile['preview_container_id'] or qa['Id'] != profile['qa_container_id']
                or not preview['State']['Running']):
            raise ValueError
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        raise ImproperlyConfigured('Cannot attest approved preview container; no write allowed.') from None


def verify_connection(connection):
    guard_config(connection.settings_dict)
    verify_instance()
    with connection.cursor() as cursor:
        cursor.execute('SELECT current_database(),current_user,rolsuper,rolcreatedb,rolcreaterole,'
            "rolreplication,rolbypassrls,current_setting('server_version_num')::int/10000 "
            'FROM pg_roles WHERE rolname=current_user')
        if cursor.fetchone() != (EXPECTED[0], EXPECTED[1], False, False, False, False, False, 17):
            raise ImproperlyConfigured('Actual SQL preview identity is unsafe.')


def unlock_connection(connection):
    verify_connection(connection)
    connection.close()
    connection.settings_dict.setdefault('OPTIONS', {})['options'] = (
        '-c default_transaction_read_only=off -c lock_timeout=5000 -c statement_timeout=60000')
    connection.ensure_connection()
    verify_connection(connection)


class LocalOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.http import HttpResponse
        try:
            if (request.META.get('REMOTE_ADDR') not in ('127.0.0.1', '::1')
                    or request.get_host() not in ('127.0.0.1:8000', 'localhost:8000')):
                return HttpResponse('Localhost only.', status=403)
            profile = read_profile()
            cookie = request.COOKIES.get('nau_local_smoke', '')
            valid_cookie = bool(re.fullmatch(r'[a-f0-9]{64}', cookie))
            allowed = profile['mode'] == 'open' or (profile['mode'] == 'smoke' and valid_cookie and hmac.compare_digest(
                cookie, profile['smoke_key']))
            if not allowed:
                return HttpResponse('Nâu đang bảo trì localhost.', status=503,
                    headers={'Cache-Control': 'no-store', 'Retry-After': '60'})
        except (ValueError, OSError, ImproperlyConfigured, DisallowedHost, KeyError):
            return HttpResponse('Local maintenance unavailable.', status=503)
        return self.get_response(request)


class SandboxSMTP:
    """Loopback capture only: no relay, auth, outbound sockets or content logging."""
    def __init__(self, port=25251):
        if port != 25251:
            raise ValueError('Unapproved sandbox port')
        self.port = port
        self.ready = threading.Event()
        self.error = False

    async def handle(self, reader, writer):
        async def reply(text):
            writer.write(text.encode('ascii') + b'\r\n')
            await writer.drain()
        data_mode, lines, size, recipients = False, [], 0, 0
        try:
            await reply('220 localhost-sandbox')
            while True:
                line = await asyncio.wait_for(reader.readline(), timeout=30)
                if not line:
                    break
                if data_mode:
                    if line in (b'.\r\n', b'.\n'):
                        require_private(OUTBOX, True)
                        if len(list(OUTBOX.glob('*.eml'))) >= 200:
                            await reply('452 Local mailbox full')
                        else:
                            path = OUTBOX / (uuid.uuid4().hex + '.eml')
                            with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'wb') as f:
                                f.write(b''.join(lines))
                            await reply('250 Captured locally; not sent to Gmail')
                        data_mode, lines, size = False, [], 0
                    else:
                        size += len(line)
                        if size > 262144:
                            await reply('552 Message too large')
                            break
                        lines.append(line[1:] if line.startswith(b'..') else line)
                    continue
                command = line.split(b' ', 1)[0].strip().upper()
                if command in (b'EHLO', b'HELO'):
                    await reply('250-localhost')
                    await reply('250 SIZE 262144')
                elif command == b'MAIL':
                    recipients = 0
                    await reply('250 OK')
                elif command == b'RCPT':
                    recipients += 1
                    await reply('250 OK' if recipients <= 10 else '452 Too many recipients')
                elif command == b'DATA' and recipients:
                    data_mode, lines, size = True, [], 0
                    await reply('354 End with dot')
                elif command in (b'RSET', b'NOOP'):
                    data_mode, lines, size, recipients = False, [], 0, 0
                    await reply('250 OK')
                elif command == b'QUIT':
                    await reply('221 Bye')
                    break
                else:
                    await reply('502 Local capture does not support this command')
        except (OSError, ValueError, asyncio.TimeoutError, ImproperlyConfigured):
            pass  # No exception text, message content or credentials are logged.
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:
                pass

    def start(self):
        require_private(OUTBOX, True)
        def work():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            try:
                self.server = self.loop.run_until_complete(asyncio.start_server(
                    self.handle, '127.0.0.1', self.port, limit=270000))
            except OSError:
                self.error = True
                self.ready.set()
                self.loop.close()
                return
            self.ready.set()
            self.loop.run_forever()
            self.loop.run_until_complete(self.server.wait_closed())
            self.loop.close()
        self.thread = threading.Thread(target=work, daemon=True)
        self.thread.start()
        if not self.ready.wait(10) or self.error:
            raise RuntimeError('Local sandbox unavailable; server not started.')

    def stop(self):
        if getattr(self, 'loop', None) and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.server.close)
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=10)


def mailbox(request, message_id=None):
    from django.contrib.auth.views import redirect_to_login
    from django.http import HttpResponseForbidden, HttpResponseNotAllowed
    from django.shortcuts import render
    from email import policy
    from email.parser import BytesParser
    from urllib.parse import urlsplit
    from catalog.permissions import has_role
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    if not has_role(request.user, 'ADMIN'):
        return HttpResponseForbidden('Chỉ quản trị được xem thư sandbox local.')
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    require_private(OUTBOX, True)
    files = sorted(OUTBOX.glob('*.eml'), key=lambda p: p.stat().st_mtime, reverse=True)[:50]
    messages, selected = [], None
    for path in files:
        require_private(path)
        msg = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
        messages.append({'id': uuid.UUID(hex=path.stem), 'subject': str(msg.get('Subject', '')), 'to': str(msg.get('To', ''))})
        if message_id and path.stem == message_id.hex:
            part = msg.get_body(preferencelist=('plain',))
            body = part.get_content() if part else ''
            links = []
            for url in re.findall(r'http://[^\s<>]+', body):
                parsed = urlsplit(url)
                if parsed.netloc == '127.0.0.1:8000' and parsed.path in (
                        '/accounts/activate/', '/accounts/password/reset/confirm/'):
                    links.append(url)
            selected = {'body': body, 'links': links}
    response = render(request, 'local/mailbox.html', {'mail': messages, 'selected': selected})
    response['Cache-Control'] = 'no-store'
    response['Referrer-Policy'] = 'no-referrer'
    return response
