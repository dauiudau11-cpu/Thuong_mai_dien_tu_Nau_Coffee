"""Create a fresh, disposable CI test DB only. Never read development credentials.

Requires a new PostgreSQL 17 service owned by nau_ci_owner. Administrator
access uses the container's local Unix socket, not an application password.
"""
import os
from pathlib import Path
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def prepare():
    if os.getenv('GITHUB_ACTIONS') != 'true' and os.getenv('NAU_CI_LOCAL') != '1':
        raise RuntimeError('CI bootstrap requires an explicit disposable CI context.')
    if os.getenv('DATABASE_URL') or any((ROOT / name).exists() for name in ['.env', '.env.test']):
        raise RuntimeError('Refusing existing database configuration; use a clean exported checkout.')
    container = os.environ.get('NAU_CI_POSTGRES_CONTAINER', '')
    if not container or not all(c.isalnum() or c in '_.-' for c in container):
        raise RuntimeError('Missing or invalid disposable PostgreSQL service ID.')

    def sql(statement):
        result = subprocess.run(['docker', 'exec', '-i', container, 'psql', '-X', '-v', 'ON_ERROR_STOP=1',
            '-U', 'nau_ci_owner', '-d', 'postgres', '-At'], input=statement, text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError('CI database operation failed; SQL and credentials suppressed. No cleanup performed.')
        return result.stdout.strip()

    identity = sql("SELECT current_database(), current_user, current_setting('server_version_num')::int / 10000;")
    if identity != 'postgres|nau_ci_owner|17':
        raise RuntimeError('Refusing unexpected CI database identity or PostgreSQL version.')
    databases = set(sql('SELECT datname FROM pg_database;').splitlines())
    if databases - {'postgres', 'template0', 'template1', 'nau_ci_owner'}:
        raise RuntimeError('Refusing a nonempty PostgreSQL cluster; existing data preserved.')
    if sql("SELECT rolname FROM pg_roles WHERE rolname IN ('nau_coffee_app','nau_coffee_test_runner');"):
        raise RuntimeError('Refusing existing application/test roles; no resources changed.')

    password = secrets.token_urlsafe(40)
    key = secrets.token_urlsafe(64)
    # token_urlsafe contains no SQL quote characters. Preserve the newly generated
    # credential privately before CREATE, so a partial failure never loses it.
    contents = (f'DJANGO_SECRET_KEY={key}\nDJANGO_DEBUG=True\n'
        'DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver\n'
        f'DATABASE_URL=postgresql://nau_coffee_test_runner:{password}@127.0.0.1:5432/nau_coffee_test\n'
        'NAU_TEST_SQLITE=False\nNAU_TEST_DATABASE_NAME=nau_coffee_test\n')
    fd = os.open(ROOT / '.env.test', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        handle.write(contents)
    sql("CREATE ROLE nau_coffee_test_runner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '" + password + "';")
    sql('CREATE DATABASE nau_coffee_test OWNER nau_coffee_test_runner;')
    sql('REVOKE ALL ON DATABASE nau_coffee_test FROM PUBLIC;')
    print('PASS: new CI-only nau_coffee_test and restricted runner role; fresh credentials written privately.')


if __name__ == '__main__':
    try:
        prepare()
    except (RuntimeError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
