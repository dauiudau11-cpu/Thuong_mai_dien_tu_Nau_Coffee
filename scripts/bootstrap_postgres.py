"""Create only NEW Nau databases/roles. Never reset existing data."""
import os
from pathlib import Path
import secrets
import subprocess
import json

class BootstrapError(Exception):
    pass

ROOT = Path(__file__).resolve().parent.parent


def sql(statement):
    result = subprocess.run([
        'docker', 'exec', '-i', 'pg_lab_postgres', 'sh', '-c',
        'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -At'],
        input=statement, text=True, capture_output=True)
    if result.returncode:
        raise BootstrapError('PostgreSQL operation failed; SQL/error output suppressed.')
    return result.stdout.strip()


def bootstrap():
    # Check Docker access before generating credentials or creating anything.
    probe = subprocess.run(['docker', 'exec', 'pg_lab_postgres', 'pg_isready'],
                           capture_output=True, text=True)
    if probe.returncode:
        raise BootstrapError('Docker access or PostgreSQL readiness failed. No resources created.')
    for filename in ['.env', '.env.test']:
        if (ROOT / filename).exists():
            raise SystemExit('Local env already exists; refusing to overwrite.')
    existing = sql("SELECT datname FROM pg_database WHERE datname IN ('nau_coffee_dev','nau_coffee_test');"
                   "SELECT rolname FROM pg_roles WHERE rolname IN ('nau_coffee_app','nau_coffee_test_runner');")
    if existing:
        raise SystemExit('Nau names already exist; refusing to modify existing roles/databases.')
    created = []
    files = []
    attempted = ''
    try:
        for db, role, filename in [('nau_coffee_dev', 'nau_coffee_app', '.env'),
                                  ('nau_coffee_test', 'nau_coffee_test_runner', '.env.test')]:
            password = secrets.token_urlsafe(40)
            contents = (f'DJANGO_DEBUG=True\nDJANGO_SECRET_KEY={secrets.token_urlsafe(64)}\n'
                        f'DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver\n'
                        f'DATABASE_URL=postgresql://{role}:{password}@127.0.0.1:5432/{db}\n'
                        'NAU_TEST_DATABASE_NAME=nau_coffee_test\n')
            fd = os.open(ROOT / filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            files.append(filename)
            if os.geteuid() == 0 and os.getenv('SUDO_UID') and os.getenv('SUDO_GID'):
                os.fchown(fd, int(os.environ['SUDO_UID']), int(os.environ['SUDO_GID']))
            with os.fdopen(fd, 'w') as handle:
                handle.write(contents)
            # Keep the generated credentials locally even if a later database step fails.
            attempted = f'create role {role}'
            sql(f"CREATE ROLE {role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '{password}';")
            created.append(f'role:{role}')
            attempted = f'create database {db}'
            sql(f'CREATE DATABASE {db} OWNER {role};')
            created.append(f'database:{db}')
            attempted = f'revoke PUBLIC on {db}'
            sql(f'REVOKE ALL ON DATABASE {db} FROM PUBLIC;')
            if db == 'nau_coffee_test':
                attempted = 'deny test runner CONNECT to nau_coffee_dev'
                sql('REVOKE CONNECT ON DATABASE nau_coffee_dev FROM nau_coffee_test_runner;')
    except (BootstrapError, OSError, KeyboardInterrupt):
        report = {'status': 'PARTIAL_FAILURE', 'confirmed_created': created,
                  'local_files': files, 'last_attempt': attempted,
                  'note': 'No cleanup performed; last attempt may need read-only verification.'}
        # Only resource names/status, never credentials or raw PostgreSQL errors.
        print(json.dumps(report, ensure_ascii=False))
        raise BootstrapError('Stopped. Preserve resources and env files; do not rerun/reset automatically.') from None
    print('Created dedicated Nau development/test databases and restricted roles. Secrets saved locally (0600).')


if __name__ == '__main__':
    try:
        bootstrap()
    except BootstrapError as exc:
        raise SystemExit(str(exc)) from None
