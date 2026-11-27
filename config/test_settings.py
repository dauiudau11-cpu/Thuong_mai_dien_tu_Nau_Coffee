"""Preview defaults read-only; external QA credentials require runner attestation."""
import os
import sys
from pathlib import Path
import dj_database_url
from dotenv import dotenv_values
from django.core.exceptions import ImproperlyConfigured
from .test_runner import validate_test_target, ACCOUNTS_QA_IDENTITY

test_file = Path(os.environ.get('NAU_QA_ENV_FILE') or (Path(__file__).resolve().parent.parent / '.env.test'))
if os.environ.get('NAU_QA_ENV_FILE'):
    try:
        private = (not test_file.is_symlink() and test_file.is_file()
                   and test_file.stat().st_mode & 0o777 == 0o600
                   and test_file.stat().st_uid == os.getuid())
    except OSError:
        private = False
    if not private:
        raise ImproperlyConfigured('QA credentials require an owned regular file with mode 0600.')
values = dotenv_values(test_file)
try:
    target = dj_database_url.parse(values.get('DATABASE_URL') or '')
    target['TEST'] = {'NAME': target.get('NAME')}
    validate_test_target(target, keepdb=True, parallel=1)
    if (target.get('NAME'), target.get('USER')) == ACCOUNTS_QA_IDENTITY and not os.environ.get('NAU_QA_ENV_FILE'):
        raise ImproperlyConfigured('Accounts QA requires explicit private QA credentials.')
except (ValueError, ImproperlyConfigured):
    raise ImproperlyConfigured('Missing or unsafe .env.test. No test database connection attempted.') from None
if not values.get('DJANGO_SECRET_KEY'):
    raise ImproperlyConfigured('Missing local test secret.')
os.environ['NAU_ENV_FILE'] = str(test_file.resolve())
os.environ['DATABASE_URL'] = values['DATABASE_URL']
os.environ['DJANGO_SECRET_KEY'] = values['DJANGO_SECRET_KEY']
os.environ['DJANGO_DEBUG'] = 'True'
os.environ['NAU_TEST_SQLITE'] = 'False'
os.environ['NAU_TEST_DATABASE_NAME'] = target['NAME']
from .settings import *  # noqa: F403,E402
DATABASES = {'default': target}
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# CLI checks/fixtures/flush/migrations are read-only, including direct call_command.
# Only the explicit preview launcher may serve application writes. Regression
# unlocks its connection separately, after independent-instance attestation.
_preview_launch = (Path(sys.argv[0]).resolve() == BASE_DIR / 'scripts/pickup_preview.py'
                   and len(sys.argv) > 1 and sys.argv[1] in ('serve', 'prepare'))
if _preview_launch and (os.environ.get('NAU_QA_ENV_FILE')
                        or str(target.get('PORT')) != '5432'):
    raise ImproperlyConfigured('Preview cannot serve or prepare the regression QA instance.')
if not _preview_launch:
    DATABASES['default'].setdefault('OPTIONS', {})['options'] = '-c default_transaction_read_only=on'
