import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / os.getenv('NAU_ENV_FILE', '.env'))
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() == 'true'
TEST_SQLITE = os.getenv('NAU_TEST_SQLITE', 'False').lower() == 'true'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if TEST_SQLITE:
        SECRET_KEY = 'isolated-test-key-never-for-deployment'
    else:
        raise ImproperlyConfigured('Set DJANGO_SECRET_KEY in local .env.')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
INSTALLED_APPS = [
    'catalog.apps.NauAdminConfig', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'catalog.apps.CatalogConfig', 'commerce.apps.CommerceConfig', 'support',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'catalog.traffic.TrafficMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEST_RUNNER = 'config.test_runner.NauTestRunner'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
              'DIRS': [BASE_DIR / 'templates'], 'APP_DIRS': True,
              'OPTIONS': {'context_processors': [
                  'django.template.context_processors.request',
                  'catalog.context_processors.standard_menu',
                  'catalog.admin_navigation.admin_navigation',
                  'django.contrib.auth.context_processors.auth',
                  'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
if TEST_SQLITE:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
else:
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ImproperlyConfigured('Set DATABASE_URL for the dedicated PostgreSQL database.')
    DATABASES = {'default': dj_database_url.parse(database_url, conn_max_age=60)}
    if os.getenv('NAU_TEST_DATABASE_NAME'):
        DATABASES['default']['TEST'] = {'NAME': os.environ['NAU_TEST_DATABASE_NAME']}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/menu/'
LOGOUT_REDIRECT_URL = '/'
if not DEBUG and not TEST_SQLITE:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
CSRF_TRUSTED_ORIGINS = [value for value in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if value]

# Staged rollout: leave disabled until catalog, BOM, backup and cutover are approved.
NAU_STANDARD_MENU_ENABLED = os.getenv('NAU_STANDARD_MENU_ENABLED', 'False').lower() == 'true'
# OFF by default. Demo delivery uses fixed fictional addresses; no Google API.
NAU_DEMO_DELIVERY_ENABLED = os.getenv('NAU_DEMO_DELIVERY_ENABLED', 'False').lower() == 'true'

# Customer accounts phase 1: enable only after approved schema/email rollout.
NAU_CUSTOMER_ACCOUNTS_ENABLED = os.getenv('NAU_CUSTOMER_ACCOUNTS_ENABLED', 'False').lower() == 'true'
NAU_ACCOUNT_EMAIL_READY = os.getenv('NAU_ACCOUNT_EMAIL_READY', 'False').lower() == 'true'
NAU_ACCOUNT_PUBLIC_ORIGIN = os.getenv('NAU_ACCOUNT_PUBLIC_ORIGIN', '')
NAU_ACCOUNT_ACTIVATION_TIMEOUT = 86400
NAU_ACCOUNT_EMAIL_COOLDOWN = 60
NAU_ACCOUNT_ALLOW_TEST_EMAIL = False
from .email_settings import email_configuration
globals().update(email_configuration(os.environ))
AUTHENTICATION_BACKENDS = (['catalog.customer_auth.CustomerModelBackend'] if NAU_CUSTOMER_ACCOUNTS_ENABLED
                           else ['django.contrib.auth.backends.ModelBackend'])

# Phase 2 is opt-in only after separately approved schema/cutover.
NAU_VOUCHERS_V2_ENABLED = os.getenv('NAU_VOUCHERS_V2_ENABLED','False').lower() == 'true'

# Django's standard password reset token TTL; independent of activation tokens.
try:
    PASSWORD_RESET_TIMEOUT = int(os.getenv('NAU_PASSWORD_RESET_TIMEOUT', '3600'))
except (ValueError,TypeError):
    raise ImproperlyConfigured('Invalid password reset timeout configuration.') from None
if not 60 <= PASSWORD_RESET_TIMEOUT <= 86400:
    raise ImproperlyConfigured('Password reset timeout must be between60and86400seconds.')

# Local first-party telemetry; no business database or external analytics writes.
NAU_TRAFFIC_ENABLED = False
NAU_TRAFFIC_ROOT = Path.home() / ".local/share/nau-coffee/traffic"

# Requires approved support policy schema/content cutover; remains OFF on preview.
NAU_POLICY_CONSENT_ENABLED = False
