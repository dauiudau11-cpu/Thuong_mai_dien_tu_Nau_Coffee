#!/usr/bin/env python3
"""Explicit Phase C localhost maintenance. No seed/flush/reset or generic DB targets."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
EVIDENCE = ROOT / 'docs/qa/2026-11-13-local-cutover'


def closed_port(port):
    with socket.socket() as sock:
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            raise RuntimeError('Approved local port is already in use; existing process preserved.') from None


def setup(local=False):
    if os.environ.get('NAU_QA_ENV_FILE') or os.environ.get('NAU_SMTP_ENV_FILE'):
        raise RuntimeError('Refusing inherited QA/live SMTP overrides.')
    for key in list(os.environ):
        if key.startswith('DJANGO_EMAIL_'):
            os.environ.pop(key)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.local_preview_settings' if local else 'config.test_settings'
    os.environ['NAU_STANDARD_MENU_ENABLED'] = 'True'
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    import django
    django.setup()
    from django.db import connection
    from config.local_preview import verify_connection
    verify_connection(connection)
    return connection


def snapshot(conn):
    def query(sql):
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    tables = query("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    seqs = query("SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename")
    import re
    assert all(re.fullmatch('[a-z0-9_]+', n) for n, in tables + seqs)
    result = {'tables': {}, 'sequences': {}}
    for table, in tables:
        result['tables'][table] = query(f'''SELECT count(*),md5(coalesce(string_agg(md5(row_to_json(t)::text),'' ORDER BY md5(row_to_json(t)::text)),'')) FROM "{table}" t''')[0]
    for seq, in seqs:
        result['sequences'][seq] = query(f'SELECT last_value,is_called FROM "{seq}"')[0]
    sqls = {
        'constraints': "SELECT t.relname,c.conname,c.contype,pg_get_constraintdef(c.oid),c.convalidated FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname='public' ORDER BY t.relname,c.conname",
        'columns': "SELECT table_name,column_name,row_number() OVER (PARTITION BY table_name ORDER BY ordinal_position) AS ordinal_position,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position",
        'indexes': "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname",
        'migrations': 'SELECT app,name FROM django_migrations ORDER BY app,name'}
    for name, sql in sqls.items():
        result[name] = query(sql)
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def schema_summary(value):
    return {'tables': len(value['tables']), 'sequences': len(value['sequences']),
        'indexes': len(value['indexes']), 'constraints': len(value['constraints']),
        'fk': sum(r[2] == 'f' for r in value['constraints'])}


def migrate():
    from config.local_preview import read_profile, require_private, unlock_connection
    profile = read_profile()
    if profile['features_enabled'] or profile['mode'] not in ('closed', 'failed'):
        raise RuntimeError('Migration requires closed maintenance with features OFF.')
    closed_port(8000)
    path = EVIDENCE / 'backup-restore-result.json'
    proof = json.loads(path.read_text())
    from datetime import datetime, timezone
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(proof['timestamp_vietnam'])).total_seconds()
    if (proof['status'] != 'PASS' or proof['tables'] != 38 or not proof['source_before_after_equal']
            or not 0 <= age < 1800 or proof['preflight']['source_database'] != 'nau_coffee_test'
            or proof['preflight']['source_port'] != 5432):
        raise RuntimeError('Missing, expired or unsafe fresh backup/restore proof.')
    archive, key = Path(proof['archive']), Path(proof['key_file'])
    for file in (archive, key):
        require_private(file)
        if not file.resolve().is_relative_to(Path.home() / '.local/share/nau-coffee'):
            raise RuntimeError('Backup must remain in the approved private local directory.')
    raw = archive.read_bytes()
    import hmac
    if (hashlib.sha256(raw).hexdigest() != proof['archive_sha256'] or raw[:8] != b'NAUENC1\n'
            or not hmac.compare_digest(raw[8:40], hmac.new(
                hashlib.sha256(b'nau-backup-hmac-v1\x00' + key.read_bytes()).digest(), raw[40:], hashlib.sha256).digest())):
        raise RuntimeError('Backup integrity check failed; no migration attempted.')
    conn = setup()
    before = snapshot(conn)
    if digest(before) != proof['source_fingerprint_sha256']:
        raise RuntimeError('Preview drift since verified backup; refusing migration.')
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(conn)
    plan = [f'{m.app_label}.{m.name}' for m, back in executor.migration_plan(executor.loader.graph.leaf_nodes())]
    expected = ['catalog.0005_counterconsent_countercustomerlink_customerprofile', 'commerce.0005_voucher_campaign_policy_v2']
    if plan != expected:
        raise RuntimeError('Migration graph differs from accepted Phase B; stop for review.')
    from django.core.management import call_command
    call_command('check', stdout=io.StringIO())
    call_command('makemigrations', check=True, dry_run=True, stdout=io.StringIO())
    # Private audit baseline, no plaintext rows or credentials.
    old_hashes = {}
    with conn.cursor() as cursor:
        for table in before['tables']:
            cursor.execute(f'SELECT md5(row_to_json(t)::text) FROM "{table}" t')
            old_hashes[table] = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()")
        if cursor.fetchone()[0]:
            raise RuntimeError('Another preview DB session exists; no writers terminated or migration attempted.')
    private = archive.parent / 'cutover-baseline.json'
    with os.fdopen(os.open(private, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), 'w') as stream:
        json.dump({'before': before, 'old_hashes': old_hashes}, stream, default=str)
    unlock_connection(conn)
    with conn.cursor() as cursor:
        cursor.execute('SELECT pg_try_advisory_lock(1312904499)')
        if not cursor.fetchone()[0]:
            raise RuntimeError('Another maintenance process owns the preview cutover lock.')
    try:
        started = time.monotonic()
        call_command('migrate', interactive=False, verbosity=0, stdout=io.StringIO(), stderr=io.StringIO())
        seconds = time.monotonic() - started
        after = snapshot(conn)
        if schema_summary(after) != {'tables':45,'sequences':44,'indexes':160,'constraints':209,'fk':64}:
            raise RuntimeError('Post-migration schema differs from rehearsal.')
        if not all(row[-1] for row in after['constraints']):
            raise RuntimeError('Unvalidated constraint after migration.')
        changes = {}
        with conn.cursor() as cursor:
            for table, old in before['tables'].items():
                cursor.execute(f'SELECT md5(row_to_json(t)::text) FROM "{table}" t')
                hashes = {row[0] for row in cursor.fetchall()}
                if not all(value in hashes for value in old_hashes[table]):
                    raise RuntimeError('An original row changed; stop without automatic restore.')
                added = after['tables'][table][0] - old[0]
                wanted = {'django_migrations':2,'django_content_type':7,'auth_permission':28}.get(table,0)
                if added != wanted:
                    raise RuntimeError('Unexpected table change after migration.')
                if added:
                    changes[table] = added
        repeat_started = time.monotonic()
        call_command('migrate', interactive=False, verbosity=0, stdout=io.StringIO(), stderr=io.StringIO())
        rerun_seconds = time.monotonic() - repeat_started
        if snapshot(conn) != after:
            raise RuntimeError('Idempotent rerun changed state.')
        final = MigrationExecutor(conn)
        if final.migration_plan(final.loader.graph.leaf_nodes()):
            raise RuntimeError('Pending migration remains.')
        result = {'status':'PASS','database':'nau_coffee_test','port':5432,'plan':plan,'seconds':round(seconds,3),
            'rerun_seconds':round(rerun_seconds,3),'schema':schema_summary(after),'metadata_added':changes,
            'original_rows_preserved':True,'pending':0,'private_baseline':str(private)}
        (EVIDENCE/'migration-result.json').write_text(json.dumps(result,indent=2))
        print(json.dumps(result | {'private_baseline':'private outside repository'}))
    finally:
        conn.close()


def serve():
    from config.local_preview import read_profile, write_profile, SandboxSMTP, unlock_connection, verify_connection
    profile = read_profile()
    if not (EVIDENCE/'migration-result.json').exists():
        raise RuntimeError('No successful local migration receipt.')
    closed_port(8000)
    closed_port(25251)
    conn = setup(local=True)
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(conn)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise RuntimeError('Schema not current; server not started.')
    unlock_connection(conn)
    from django.db.backends.signals import connection_created
    def observe(sender, connection, **kwargs):
        verify_connection(connection)
    connection_created.connect(observe)
    sink = SandboxSMTP()
    sink.start()
    profile['pid'] = os.getpid()
    write_profile(profile)
    print('Verified localhost preview: http://127.0.0.1:8000/ ; email captured locally only.', flush=True)
    try:
        from django.core.management import call_command
        call_command('runserver','127.0.0.1:8000',use_reloader=False)
    finally:
        sink.stop()
        conn.close()


def main():
    os.chdir(ROOT)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect','migrate','serve'])
    args = parser.parse_args()
    if args.action == 'migrate':
        migrate()
    elif args.action == 'serve':
        serve()
    else:
        conn = setup()
        from config.local_preview import read_profile
        from django.db.migrations.executor import MigrationExecutor
        ex = MigrationExecutor(conn)
        print(json.dumps({'database':conn.settings_dict['NAME'],'port':conn.settings_dict['PORT'],
            'schema':schema_summary(snapshot(conn)), 'pending':[f'{m.app_label}.{m.name}' for m,b in ex.migration_plan(ex.loader.graph.leaf_nodes())],
            'features_enabled':read_profile()['features_enabled'],'mode':read_profile()['mode']}))
        conn.close()


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    try:
        main()
    except Exception as error:
        import traceback
        print(json.dumps({'status':'STOP','type':type(error).__name__,
            'locations':[{'file':Path(f.filename).name,'line':f.lineno} for f in traceback.extract_tb(error.__traceback__)[-3:]],
            'message':'Secrets withheld; no automatic reset/restore/retry.'}),file=sys.stderr)
        raise SystemExit(1) from None
