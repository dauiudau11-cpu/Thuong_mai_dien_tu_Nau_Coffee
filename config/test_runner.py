"""Use only the pre-created dedicated PostgreSQL test DB; never CREATE/DROP DB."""
import json
import subprocess
from datetime import datetime, timezone as datetime_timezone
from pathlib import PurePosixPath
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db import connections
from django.test.runner import DiscoverRunner

LEGACY_TEST_IDENTITY = ('nau_coffee_test', 'nau_coffee_test_runner')
ACCOUNTS_QA_IDENTITY = ('nau_coffee_qa_accounts', 'nau_coffee_qa_accounts_runner')
TEST_IDENTITIES = {LEGACY_TEST_IDENTITY, ACCOUNTS_QA_IDENTITY}


def validate_test_target(config, *, keepdb, parallel):
    if (config.get('ENGINE') == 'django.db.backends.sqlite3'
            and config.get('NAME') == ':memory:'):
        return 'sqlite'
    if (config.get('ENGINE') != 'django.db.backends.postgresql'
            or (config.get('NAME'), config.get('USER')) not in TEST_IDENTITIES
            or config.get('TEST', {}).get('NAME') != config.get('NAME')
            or config.get('HOST') not in ('127.0.0.1', 'localhost')
            or not keepdb or parallel not in (0, 1)):
        raise ImproperlyConfigured(
            'Refusing unsafe test target. Use config.test_settings, dedicated '
            'nau_coffee_test_runner/nau_coffee_test, --keepdb and no parallel workers.')
    if (config.get('NAME'), config.get('USER')) == ACCOUNTS_QA_IDENTITY and (
            config.get('HOST') != '127.0.0.1' or str(config.get('PORT')) != '55441'):
        raise ImproperlyConfigured('Accounts QA permits only its dedicated loopback 55441 endpoint.')
    return 'postgresql'


def verify_qa_instance(config):
    """Fail before connecting: Docker attests a separate cluster, not just DB names.

    Fixed local QA endpoint only; no arbitrary env override or shared PGDATA.
    Docker unavailable, missing container or unexpected binding => refuse writes.
    """
    validate_test_target(config, keepdb=True, parallel=1)
    if config.get('HOST') != '127.0.0.1' or str(config.get('PORT')) != '55441':
        raise ImproperlyConfigured('Regression refuses preview PostgreSQL; verified QA port 55441 required.')
    try:
        result = subprocess.run(
            ['docker', 'inspect', 'nau_localization_qa_20261111', 'pg_lab_postgres'],
            capture_output=True, text=True, check=True, timeout=10)
        qa, preview = json.loads(result.stdout)
        bindings = qa['NetworkSettings']['Ports']['5432/tcp']
        qa_mounts = {m['Source'] for m in qa['Mounts'] if m['Destination'] == '/var/lib/postgresql/data'}
        preview_mounts = {m['Source'] for m in preview['Mounts'] if m['Destination'] == '/var/lib/postgresql/data'}
        safe = (qa['Name'] == '/nau_localization_qa_20261111'
                and preview['Name'] == '/pg_lab_postgres'
                and qa['Id'] != preview['Id'] and qa['State']['Running']
                and bindings == [{'HostIp': '127.0.0.1', 'HostPort': '55441'}]
                and qa_mounts and preview_mounts
                and not any(PurePosixPath(a).is_relative_to(b) or PurePosixPath(b).is_relative_to(a)
                            for a in qa_mounts for b in preview_mounts))
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError):
        raise ImproperlyConfigured('Cannot attest independent QA PostgreSQL; no writes permitted.') from None
    if not safe:
        raise ImproperlyConfigured('QA PostgreSQL is not independently isolated; no writes permitted.')


def verify_qa_identity(conn):
    """Attest storage before opening SQL, then verify the actual limited PG17 role."""
    if validate_test_target(conn.settings_dict, keepdb=True, parallel=1) != 'postgresql':
        raise ImproperlyConfigured('QA identity requires PostgreSQL.')
    verify_qa_instance(conn.settings_dict)
    expected = (conn.settings_dict['NAME'], conn.settings_dict['USER'], False, False, False)
    with conn.cursor() as cursor:
        cursor.execute('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole '
                       'FROM pg_roles WHERE rolname=current_user')
        if cursor.fetchone() != expected:
            raise ImproperlyConfigured('Actual PostgreSQL test identity is unsafe.')
        cursor.execute("SELECT current_setting('server_version_num')::int / 10000, rolreplication, rolbypassrls "
                       'FROM pg_roles WHERE rolname=current_user')
        if cursor.fetchone() != (17, False, False):
            raise ImproperlyConfigured('QA requires PostgreSQL 17 and no replication/RLS bypass.')
        cursor.execute("SELECT count(*) FROM pg_database WHERE datname='nau_coffee_dev'")
        if cursor.fetchone() != (0,):
            raise ImproperlyConfigured('QA cluster must contain no development database.')


def unlock_verified_qa(conn):
    """Only call after attestation; re-attest immediately before writable reconnect."""
    verify_qa_identity(conn)
    conn.close()
    conn.settings_dict.setdefault('OPTIONS', {})['options'] = '-c default_transaction_read_only=off'
    conn.ensure_connection()


class NauTestRunner(DiscoverRunner):
    def setup_test_environment(self, **kwargs):
        fixed_now = datetime(2026, 11, 20, 3, 0, tzinfo=datetime_timezone.utc)
        self._clock_patch = patch('django.utils.timezone.now', return_value=fixed_now)
        self._clock_patch.start()
        return super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        try:
            return super().teardown_test_environment(**kwargs)
        finally:
            self._clock_patch.stop()

    def setup_databases(self, **kwargs):
        if set(connections) != {'default'}:
            raise ImproperlyConfigured('Tests permit only one dedicated database alias.')
        conn = connections['default']
        backend = validate_test_target(conn.settings_dict, keepdb=self.keepdb, parallel=self.parallel)
        if backend == 'sqlite':
            return super().setup_databases(**kwargs)
        verify_qa_identity(conn)
        # Existing QA schema only. Never migrate implicitly during regression.
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(conn)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):
            raise ImproperlyConfigured('QA schema has pending migrations; regression refused.')
        unlock_verified_qa(conn)
        conn._test_serialized_contents = conn.creation.serialize_db_to_string()
        return []

    def teardown_databases(self, old_config, **kwargs):
        conn = connections['default']
        if conn.vendor == 'sqlite':
            return super().teardown_databases(old_config, **kwargs)
        # Keep dedicated test database and schema. TestCase rollback/TransactionTestCase
        # cleanup affect this test database only.
        conn.close()
        conn.settings_dict.setdefault('OPTIONS', {})['options'] = '-c default_transaction_read_only=on'
