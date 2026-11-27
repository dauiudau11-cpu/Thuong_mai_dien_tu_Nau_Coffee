"""Explicit local sandbox only. CLI stays READ ONLY; verified launcher unlocks writes."""
import os
from django.core.exceptions import ImproperlyConfigured
from .test_settings import *  # noqa: F403
from .local_preview import read_profile, guard_config

if os.environ.get('NAU_QA_ENV_FILE') or os.environ.get('NAU_SMTP_ENV_FILE'):
    raise ImproperlyConfigured('Local preview refuses QA or live SMTP credential overrides.')
guard_config(DATABASES['default'])
profile = read_profile()
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
ROOT_URLCONF = 'config.local_preview_urls'
MIDDLEWARE = ['config.local_preview.LocalOnlyMiddleware'] + MIDDLEWARE
NAU_STANDARD_MENU_ENABLED = True
NAU_CUSTOMER_ACCOUNTS_ENABLED = profile['features_enabled']
NAU_VOUCHERS_V2_ENABLED = profile['features_enabled']
AUTHENTICATION_BACKENDS = ['catalog.customer_auth.CustomerModelBackend'] if profile['features_enabled'] else ['django.contrib.auth.backends.ModelBackend']
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST, EMAIL_PORT = '127.0.0.1', 25251
EMAIL_HOST_USER = EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = EMAIL_USE_SSL = False
EMAIL_TIMEOUT = 15
DEFAULT_FROM_EMAIL = 'Nâu Coffee | Hỗ trợ khách hàng <naucoffee.official@gmail.com>'
NAU_ACCOUNT_ALLOW_TEST_EMAIL = True
NAU_ACCOUNT_EMAIL_READY = profile['features_enabled']
NAU_ACCOUNT_PUBLIC_ORIGIN = 'http://127.0.0.1:8000'
SECURE_SSL_REDIRECT = SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
CSRF_TRUSTED_ORIGINS = ['http://127.0.0.1:8000', 'http://localhost:8000']

NAU_TRAFFIC_ENABLED = True

# Operator enables only after approved policy schema/publication cutover.
NAU_POLICY_CONSENT_ENABLED = profile.get('policy_enabled', False)
