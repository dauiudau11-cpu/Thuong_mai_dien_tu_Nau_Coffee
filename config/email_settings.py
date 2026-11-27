"""Explicit, private SMTP configuration; never load database or feature credentials."""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import dotenv_values

SMTP_KEYS = frozenset({'DJANGO_EMAIL_BACKEND','DJANGO_EMAIL_HOST','DJANGO_EMAIL_PORT',
    'DJANGO_EMAIL_HOST_USER','DJANGO_EMAIL_HOST_PASSWORD','DJANGO_EMAIL_USE_TLS',
    'DJANGO_EMAIL_USE_SSL','DJANGO_EMAIL_TIMEOUT','DJANGO_DEFAULT_FROM_EMAIL',
    'NAU_ACCOUNT_EMAIL_READY','NAU_ACCOUNT_PUBLIC_ORIGIN'})


def email_configuration(environ):
    private = {}
    if environ.get('NAU_SMTP_ENV_FILE'):
        path = Path(environ['NAU_SMTP_ENV_FILE'])
        try:
            safe = (path.is_file() and not path.is_symlink() and path.stat().st_uid == os.getuid()
                    and path.stat().st_mode & 0o777 == 0o600)
        except OSError:
            safe = False
        if not safe:
            raise ImproperlyConfigured('SMTP secrets require an owned regular file with mode 0600.')
        private = dotenv_values(path, interpolate=False)
        if set(private) - SMTP_KEYS or any(v is None for v in private.values()):
            raise ImproperlyConfigured('SMTP file contains unsupported settings; no values disclosed.')
    def value(name, default):
        return environ.get(name, private.get(name, default))
    def boolean(name, default):
        raw = value(name, default)
        if str(raw).lower() not in ('true','false'):
            raise ImproperlyConfigured('SMTP boolean configuration is invalid; values withheld.')
        return str(raw).lower() == 'true'
    try:
        port = int(value('DJANGO_EMAIL_PORT','587'))
        timeout = int(value('DJANGO_EMAIL_TIMEOUT','15'))
        if not 1 <= port <= 65535 or not 1 <= timeout <= 60:raise ValueError
    except (ValueError,TypeError):
        raise ImproperlyConfigured('SMTP port/timeout configuration is invalid; values withheld.') from None
    tls, ssl = boolean('DJANGO_EMAIL_USE_TLS','True'), boolean('DJANGO_EMAIL_USE_SSL','False')
    if tls and ssl:raise ImproperlyConfigured('SMTP cannot enable both TLS and SSL.')
    password = value('DJANGO_EMAIL_HOST_PASSWORD','')
    if value('DJANGO_EMAIL_HOST','smtp.gmail.com') == 'smtp.gmail.com':
        password = password.replace(' ','')
    return dict(EMAIL_BACKEND=value('DJANGO_EMAIL_BACKEND','django.core.mail.backends.smtp.EmailBackend'),
        EMAIL_HOST=value('DJANGO_EMAIL_HOST','smtp.gmail.com'), EMAIL_PORT=port,
        EMAIL_HOST_USER=value('DJANGO_EMAIL_HOST_USER','naucoffee.official@gmail.com'),
        EMAIL_HOST_PASSWORD=password,
        EMAIL_USE_TLS=tls,EMAIL_USE_SSL=ssl,EMAIL_TIMEOUT=timeout,
        DEFAULT_FROM_EMAIL=value('DJANGO_DEFAULT_FROM_EMAIL','Nâu Coffee <naucoffee.official@gmail.com>'),
        NAU_ACCOUNT_EMAIL_READY=boolean('NAU_ACCOUNT_EMAIL_READY','False'),
        NAU_ACCOUNT_PUBLIC_ORIGIN=value('NAU_ACCOUNT_PUBLIC_ORIGIN',''))
