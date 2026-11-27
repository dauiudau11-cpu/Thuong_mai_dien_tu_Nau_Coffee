"""Read-only identity/privilege checks; never print connection strings or secrets."""
from pathlib import Path
from dotenv import dotenv_values
import dj_database_url
import psycopg

ROOT = Path(__file__).resolve().parent.parent


def verify():
    for filename, name, role, other in [('.env', 'nau_coffee_dev', 'nau_coffee_app', 'nau_coffee_test'),
            ('.env.test', 'nau_coffee_test', 'nau_coffee_test_runner', 'nau_coffee_dev')]:
        try:
            url = dotenv_values(ROOT / filename).get('DATABASE_URL', '')
            target = dj_database_url.parse(url)
            if (target.get('NAME') != name or target.get('USER') != role
                    or target.get('HOST') != '127.0.0.1' or str(target.get('PORT')) != '5432'):
                raise ValueError('Unexpected database target')
            with psycopg.connect(url, connect_timeout=5, options='-c default_transaction_read_only=on') as conn:
                with conn.cursor() as cursor:
                    cursor.execute('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole '
                                   'FROM pg_roles WHERE rolname=current_user')
                    if cursor.fetchone() != (name, role, False, False, False):
                        raise ValueError('Unexpected identity or privileges')
                    cursor.execute('SELECT has_database_privilege(current_user, %s, %s)', [other, 'CONNECT'])
                    if cursor.fetchone()[0]:
                        raise ValueError('Cross-database CONNECT unexpectedly allowed')
                    cursor.execute("SELECT current_setting('server_version')")
                    version = cursor.fetchone()[0]
                    if not version.startswith('17.'):
                        raise ValueError('Expected PostgreSQL 17')
            print(f'PASS: {name} / {role}; PostgreSQL 17; restricted role; no CONNECT to {other}.')
        except Exception:
            raise SystemExit(f'FAIL: connection/identity/isolation check for {name}. Details suppressed to protect secrets.') from None


if __name__ == '__main__':
    verify()
