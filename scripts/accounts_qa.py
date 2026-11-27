#!/usr/bin/env python3
"""Explicit Accounts QA provisioning/migration; no preview/dev credentials are loaded.

provision: new objects only, through the independently attested QA container.
migrate: only the exact new QA identity, re-attested before enabling writes.
inspect: read-only SQL checks. No DROP/reset/credential rotation path exists.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from config.test_runner import ACCOUNTS_QA_IDENTITY, validate_test_target, verify_qa_instance

CONTAINER = 'nau_localization_qa_20261111'
ENV_FILE = ROOT / '.env.qa.accounts'
EVIDENCE = ROOT / os.environ.get('NAU_ACCOUNTS_QA_ROOT', 'docs/qa/2026-11-12-accounts-postgresql')
DB_NAME, ROLE = ACCOUNTS_QA_IDENTITY
CONFIG = {'ENGINE': 'django.db.backends.postgresql', 'NAME': DB_NAME, 'USER': ROLE,
          'HOST': '127.0.0.1', 'PORT': '55441', 'TEST': {'NAME': DB_NAME}}


def attest_container():
    validate_test_target(CONFIG, keepdb=True, parallel=1)
    verify_qa_instance(CONFIG)


def admin_sql(statement, *, database='postgres'):
    if database not in ('postgres', 'nau_coffee_test', DB_NAME):
        raise RuntimeError('Unapproved QA database.')
    result = subprocess.run(['docker', 'exec', '-i', CONTAINER, 'psql', '-X', '-qAt', '-v',
        'ON_ERROR_STOP=1', '-U', 'postgres', '-d', database], input=statement,
        text=True, capture_output=True, timeout=60)
    if result.returncode:
        # Never emit stderr, SQL, passwords or a subprocess exception with SQL input.
        raise RuntimeError('QA administration failed; details suppressed. Existing resources preserved.')
    return result.stdout.strip()


def protected_old_qa():
    attest_container()
    tables = admin_sql("BEGIN READ ONLY; SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename; ROLLBACK;", database='nau_coffee_test').splitlines()
    if not tables or not all(re.fullmatch(r'[a-z0-9_]+', name) for name in tables):
        raise RuntimeError('Cannot fingerprint original QA schema safely.')
    statements = ['BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;']
    for name in tables:
        statements.append(f"SELECT '{name}', count(*), md5(coalesce(string_agg(md5(row_to_json(t)::text),'' ORDER BY md5(row_to_json(t)::text)),'')) FROM {name} t;")
    statements.append('ROLLBACK;')
    rows = admin_sql('\n'.join(statements), database='nau_coffee_test').splitlines()
    role = admin_sql("BEGIN READ ONLY; SELECT rolname,rolsuper,rolcreatedb,rolcreaterole,rolcanlogin FROM pg_roles WHERE rolname='nau_coffee_test_runner'; ROLLBACK;")
    return {'tables': len(tables), 'rows_digest': hashlib.sha256('\n'.join(rows).encode()).hexdigest(), 'role_attributes': role}


def provision():
    attest_container()
    if ENV_FILE.exists():
        raise RuntimeError('QA credentials file already exists; refusing overwrite or credential changes.')
    if subprocess.run(['git', 'check-ignore', '--quiet', str(ENV_FILE)], cwd=ROOT).returncode:
        raise RuntimeError('QA credentials path is not Git ignored.')
    identity = admin_sql("BEGIN READ ONLY; SELECT current_user,rolsuper,rolcreaterole,rolcreatedb,current_setting('server_version_num')::int/10000 FROM pg_roles WHERE rolname=current_user; ROLLBACK;")
    if identity != 'postgres|t|t|t|17':
        raise RuntimeError('QA administrative role is insufficient or unexpected; no objects created.')
    existing = admin_sql(f"BEGIN READ ONLY; SELECT rolname FROM pg_roles WHERE rolname='{ROLE}'; SELECT datname FROM pg_database WHERE datname='{DB_NAME}'; ROLLBACK;")
    if existing:
        raise RuntimeError('Approved QA objects already exist; no account, password or database modified.')
    before = protected_old_qa()
    password, key = secrets.token_urlsafe(48), secrets.token_urlsafe(64)
    # File first: preserve new credentials even if a subsequent DDL step fails.
    fd = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(f'DATABASE_URL=postgresql://{ROLE}:{password}@127.0.0.1:55441/{DB_NAME}\nDJANGO_SECRET_KEY={key}\n')
        stream.flush();os.fsync(stream.fileno())
    attest_container()
    # These settings affect only this QA admin session; errors must not log a secret statement.
    admin_sql("SET log_statement='none'; SET log_min_duration_statement=-1; SET log_min_error_statement='panic';\n"
        f"CREATE ROLE {ROLE} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD '{password}';")
    admin_sql(f'CREATE DATABASE {DB_NAME} OWNER postgres TEMPLATE template0 ENCODING \'UTF8\';')
    admin_sql(f'REVOKE ALL ON DATABASE {DB_NAME} FROM PUBLIC; GRANT CONNECT ON DATABASE {DB_NAME} TO {ROLE};')
    admin_sql(f'GRANT USAGE, CREATE ON SCHEMA public TO {ROLE};', database=DB_NAME)
    if protected_old_qa() != before:
        raise RuntimeError('Original QA fingerprint changed; stop for review. No cleanup performed.')
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE/'provision.json').write_text(json.dumps({'database':DB_NAME,'role':ROLE,'port':55441,
        'credentials_mode':'0600','credentials_git_ignored':True,'role_superuser':False,'role_createdb':False,
        'role_createrole':False,'role_replication':False,'role_bypassrls':False,'database_owner':'postgres',
        'old_qa_before':before,'old_qa_after':before,'original_qa_preserved':True},indent=2)+'\n')
    print('PASS: new QA database/limited login provisioned; credentials private 0600, Git ignored; original QA preserved.')


def setup_django():
    if not ENV_FILE.is_file() or ENV_FILE.stat().st_mode & 0o777 != 0o600:
        raise RuntimeError('Missing or unsafe QA credential file permissions.')
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.test_settings'
    os.environ['NAU_QA_ENV_FILE'] = str(ENV_FILE)
    import django
    django.setup()
    from django.db import connection
    if (connection.settings_dict['NAME'], connection.settings_dict['USER']) != ACCOUNTS_QA_IDENTITY:
        raise RuntimeError('Accounts maintenance permits only the new QA identity.')
    return connection


def inspect_or_migrate(*, apply=False):
    conn = setup_django()
    from config.test_runner import verify_qa_identity, unlock_verified_qa
    from django.db.migrations.executor import MigrationExecutor
    verify_qa_identity(conn)
    executor = MigrationExecutor(conn)
    before = [f'{m.app_label}.{m.name}' for m, backward in executor.migration_plan(executor.loader.graph.leaf_nodes())]
    if apply:
        unlock_verified_qa(conn)
        try:
            from django.core.management import call_command
            call_command('migrate', database='default', interactive=False, verbosity=1)
        finally:
            conn.close()
            conn.settings_dict.setdefault('OPTIONS', {})['options'] = '-c default_transaction_read_only=on'
    verify_qa_identity(conn)
    executor = MigrationExecutor(conn)
    after = [f'{m.app_label}.{m.name}' for m, backward in executor.migration_plan(executor.loader.graph.leaf_nodes())]
    with conn.cursor() as cursor:
        cursor.execute('SHOW transaction_read_only');read_only = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM pg_tables WHERE schemaname='public'");tables=cursor.fetchone()[0]
        cursor.execute("SELECT pg_get_userbyid(datdba)=current_user FROM pg_database WHERE datname=current_database()")
        owns_database=cursor.fetchone()[0]
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE/('migration.json' if apply else 'inspect.json')).write_text(json.dumps({
        'database':DB_NAME,'role':ROLE,'port':55441,'pending_before':before,'pending_after':after,
        'tables':tables,'read_only_after':read_only,'runner_owns_database':owns_database,
        'catalog_0005_applied':('catalog','0005_counterconsent_countercustomerlink_customerprofile') in executor.loader.applied_migrations},indent=2)+'\n')
    print(f'PASS: Accounts QA identity attested; tables={tables}, pending={len(after)}, read-only restored={read_only}.')
    conn.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['provision','inspect','migrate','verify-original'])
    args=parser.parse_args()
    if args.action=='provision':provision()
    elif args.action=='verify-original':
        original=json.loads((ROOT/'docs/qa/2026-11-12-accounts-postgresql/provision.json').read_text())['old_qa_before']
        if protected_old_qa()!=original:raise RuntimeError('Original QA changed; investigate before proceeding.')
        print('PASS: original QA tables/data/role attributes unchanged.')
    else:inspect_or_migrate(apply=args.action=='migrate')


if __name__=='__main__':
    sys.dont_write_bytecode=True
    try:main()
    except RuntimeError as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(1) from None
    except Exception:
        print('STOP: Accounts QA operation refused/failed. SQL and secrets suppressed; no automatic cleanup. Review safe preflight.',file=sys.stderr)
        raise SystemExit(1) from None
