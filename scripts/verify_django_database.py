"""Confirm Django's actual development connection with a read-only SELECT."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'


def verify():
    try:
        import django
        django.setup()
        from django.db import connection
        config = connection.settings_dict
        if (config['ENGINE'] != 'django.db.backends.postgresql'
                or config['NAME'] != 'nau_coffee_dev' or config['USER'] != 'nau_coffee_app'
                or config['HOST'] != '127.0.0.1' or str(config['PORT']) != '5432'):
            raise ValueError('Unsafe target')
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole '
                           'FROM pg_roles WHERE rolname=current_user')
            if cursor.fetchone() != ('nau_coffee_dev', 'nau_coffee_app', False, False, False):
                raise ValueError('Unsafe identity')
        print('PASS: Django connected to nau_coffee_dev as nau_coffee_app; restricted role.')
    except Exception:
        raise SystemExit('FAIL: Django development database verification; details suppressed to protect secrets.') from None
    finally:
        if 'connection' in locals():
            connection.close()


if __name__ == '__main__':
    verify()
