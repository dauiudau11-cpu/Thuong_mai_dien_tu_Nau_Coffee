"""Approved localhost policy cutover. Exact preview identity, encrypted restore proof.
No arbitrary database target, no reset/seed/drop, no live mail or remote Git actions.
"""
import argparse, hashlib, hmac, io, json, os, re, secrets, shutil, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
BASE = Path.home() / '.local/share/nau-coffee/policy-final-20261117'
KEYS = Path.home() / '.local/share/nau-coffee/policy-final-keys-20261117'
E = ROOT / 'docs/qa/2026-11-17-policy-final'
PENDING = ['support.0003_policyrevision_consentevent', 'support.0004_policy_evidence_guards']

def require(condition, message='Cutover safety condition failed'):
    if not condition:
        raise RuntimeError(message)

def write_private(path, value):
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 384), 'w') as f:
        json.dump(value, f, default=str)
        f.flush()
        os.fsync(f.fileno())

def setup():
    os.chdir(ROOT)
    from scripts.local_feature_preview import setup as connect, closed_port
    from config.local_preview import read_profile, write_profile
    closed_port(8000)
    closed_port(25251)
    conn = connect(local=True)
    p = read_profile()
    if p['mode'] not in ('closed', 'failed') or p.get('policy_enabled', False):
        raise RuntimeError('Closed maintenance and policy OFF required.')
    return conn

def run(args, data=None):
    r = subprocess.run(args, input=data, capture_output=True, timeout=180)
    if r.returncode:
        raise RuntimeError('Command failed; private SQL/data/stderr withheld. No automatic restore/retry.')
    return r.stdout

def docker_sql(container, db, sql, readonly=True):
    require(container in ('pg_lab_postgres', 'nau_localization_qa_20261111'))
    if container == 'pg_lab_postgres':
        require(db == 'nau_coffee_test' and readonly)
    else:
        require(db in ('postgres', 'nau_coffee_qa_accounts') or re.fullmatch('nau_policy_restore_20261117_[a-f0-9]{8}', db))
    text = "SET TIME ZONE 'UTC';\nBEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n" + sql + '\nROLLBACK;' if readonly else sql
    return run(['docker', 'exec', '-i', container, 'psql', '-X', '-qAt', '-v', 'ON_ERROR_STOP=1', '-U', ('nau_coffee_test_runner' if container=='pg_lab_postgres' else 'postgres'), '-d', db], text.encode()).decode().strip()

def canonical_constraint(table,name,definition):
    if table=='commerce_vouchercampaign' and name=='voucher_v2_audience':
        compact=definition.replace('::character varying','').replace('::text[]','').replace('::text','').replace('(','').replace(')','')
        require(' '.join(compact.split())=="CHECK audience = ANY ARRAY['PUBLIC', 'PRIVATE']",'Unexpected voucher audience rule; refusing normalization')
        return "CHECK (audience IN ('PUBLIC', 'PRIVATE'))"
    return definition

def fingerprint(container, db):

    def q(sql):
        return json.loads(docker_sql(container, db, "SELECT coalesce(json_agg(row_to_json(q)),'[]') FROM (" + sql + ') q;'))
    tables = q("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    result = {'tables': {}, 'sequences': {}}
    for row in tables:
        name = row['tablename']
        require(re.fullmatch('[a-z0-9_]+', name))
        result['tables'][name] = q(f'''SELECT count(*) AS count,md5(coalesce(string_agg(md5(row_to_json(t)::text),'' ORDER BY md5(row_to_json(t)::text)),'')) AS hash FROM "{name}" t''')
    for row in q("SELECT sequencename FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename"):
        n = row['sequencename']
        require(re.fullmatch('[a-z0-9_]+', n))
        result['sequences'][n] = q(f'SELECT last_value,is_called FROM "{n}"')
    for name, sql in {'columns': "SELECT table_name,column_name,row_number() OVER (PARTITION BY table_name ORDER BY ordinal_position) AS ordinal_position,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position", 'constraints': "SELECT t.relname,c.conname,c.contype,pg_get_constraintdef(c.oid),c.convalidated FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname='public' ORDER BY t.relname,c.conname", 'indexes': "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY tablename,indexname", 'migrations': 'SELECT app,name FROM django_migrations ORDER BY app,name'}.items():
        result[name] = q(sql)
    for row in result['constraints']:
        row['pg_get_constraintdef']=canonical_constraint(row['relname'],row['conname'],row['pg_get_constraintdef'])
    return result

def backup():
    c = setup()
    from scripts.local_feature_preview import snapshot, digest
    from config.local_preview import require_private
    from django.db.migrations.executor import MigrationExecutor
    ex = MigrationExecutor(c)
    require([f'{m.app_label}.{m.name}' for m, b in ex.migration_plan(ex.loader.graph.leaf_nodes())] == PENDING)
    for p in [BASE, KEYS]:
        p.mkdir(mode=448, exist_ok=True)
        require_private(p, True)
    with c.cursor() as cur:
        cur.execute('SELECT pg_database_size(current_database())')
        size = cur.fetchone()[0]
    require(shutil.disk_usage(BASE).free > max(size * 3, 100 * 1024 * 1024))
    tag = uuid.uuid4().hex[:8]
    folder = BASE / tag
    folder.mkdir(mode=448)
    keydir = KEYS / tag
    keydir.mkdir(mode=448)
    key = keydir / 'archive.key'
    with os.fdopen(os.open(key, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 384), 'w') as f:
        f.write(secrets.token_urlsafe(64))
    before = snapshot(c)
    require(len(before['tables']) == 45)
    hashes = {}
    with c.cursor() as cur:
        for table in before['tables']:
            projection = "(to_jsonb(t)-'last_login')::text" if table == 'auth_user' else 'row_to_json(t)::text'
            cur.execute(f'SELECT md5({projection}) FROM "{table}" t')
            hashes[table] = [x[0] for x in cur.fetchall()]
    write_private(folder / 'baseline.json', {'snapshot': before, 'old_rows': hashes})
    source_before = fingerprint('pg_lab_postgres', 'nau_coffee_test')
    qa_before = fingerprint('nau_localization_qa_20261111', 'nau_coffee_qa_accounts')
    dump = run(['docker', 'exec', 'pg_lab_postgres', 'pg_dump', '-U', 'nau_coffee_test_runner', '--format=custom', 'nau_coffee_test'])
    crypto = ['openssl', 'enc', '-aes-256-cbc', '-pbkdf2', '-iter', '200000', '-salt', '-pass', 'file:' + str(key)]
    encrypted = run(crypto, dump)
    mac_key = hashlib.sha256(b'nau-backup-hmac-v1\x00' + key.read_bytes()).digest()
    payload = b'NAUENC1\n' + hmac.new(mac_key, encrypted, hashlib.sha256).digest() + encrypted
    archive = folder / 'preview.dump.enc'
    with os.fdopen(os.open(archive, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 384), 'wb') as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    require(hmac.compare_digest(payload[8:40], hmac.new(mac_key, payload[40:], hashlib.sha256).digest()))
    restored = run(crypto[:2] + ['-d'] + crypto[2:], payload[40:])
    require(hashlib.sha256(restored).digest() == hashlib.sha256(dump).digest())
    target = 'nau_policy_restore_20261117_' + tag
    require(docker_sql('nau_localization_qa_20261111', 'postgres', f"SELECT count(*) FROM pg_database WHERE datname='{target}';") == '0')
    docker_sql('nau_localization_qa_20261111', 'postgres', f'CREATE DATABASE {target} OWNER postgres TEMPLATE template0 ALLOW_CONNECTIONS false;', False)
    docker_sql('nau_localization_qa_20261111', 'postgres', f'REVOKE ALL ON DATABASE {target} FROM PUBLIC;', False)
    require(docker_sql('nau_localization_qa_20261111','postgres',f"SELECT has_database_privilege('nau_coffee_qa_accounts_runner','{target}','CONNECT');")=='f')
    docker_sql('nau_localization_qa_20261111','postgres',f'ALTER DATABASE {target} ALLOW_CONNECTIONS true;',False)
    run(['docker', 'exec', '-i', 'nau_localization_qa_20261111', 'pg_restore', '-U', 'postgres', '--single-transaction', '--exit-on-error', '--no-owner', '--no-acl', '-d', target], restored)
    require(fingerprint('nau_localization_qa_20261111', target) == source_before)
    require(fingerprint('pg_lab_postgres', 'nau_coffee_test') == source_before and snapshot(c) == before)
    require(fingerprint('nau_localization_qa_20261111', 'nau_coffee_qa_accounts') == qa_before)
    receipt = {'status': 'PASS', 'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'archive': str(archive), 'key': str(key), 'baseline': str(folder / 'baseline.json'), 'archive_sha256': hashlib.sha256(payload).hexdigest(), 'source_sha256': digest(before), 'restore_target': target, 'tables': 45, 'sequences': 44, 'source_restore_schema_data_sequences_equal': True, 'main_qa_unchanged': True, 'plaintext_dump_on_disk': False,'metadata_normalization':['logical column order ignores dropped physical ordinal gaps','exact PUBLIC/PRIVATE varchar-array cast deparser variants only']}
    write_private(folder / 'receipt.json', receipt)
    pointer = BASE / 'active.json'
    if pointer.exists():
        require_private(pointer)
        temporary = BASE / ('active-' + tag + '.json')
        write_private(temporary, {'receipt': str(folder / 'receipt.json')})
        os.replace(temporary, pointer)
    else:
        write_private(pointer, {'receipt': str(folder / 'receipt.json')})
    public = {k: v for k, v in receipt.items() if k not in ('archive', 'key', 'baseline')}
    (E / 'backup-restore.json').write_text(json.dumps(public, indent=2))
    print(json.dumps(public))
    c.close()

def load_receipt():
    from config.local_preview import require_private
    require_private(BASE, True)
    require_private(BASE / 'active.json')
    path = Path(json.loads((BASE / 'active.json').read_text())['receipt'])
    require_private(path)
    r = json.loads(path.read_text())
    require(path.resolve().is_relative_to(BASE.resolve()) and r['status'] == 'PASS')
    for field in ['archive', 'key', 'baseline']:
        require_private(Path(r[field]))
    raw = Path(r['archive']).read_bytes()
    key = Path(r['key']).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == r['archive_sha256'] and raw[:8] == b'NAUENC1\n')
    require(hmac.compare_digest(raw[8:40], hmac.new(hashlib.sha256(b'nau-backup-hmac-v1\x00' + key).digest(), raw[40:], hashlib.sha256).digest()))
    return r

def migrate():
    c = setup()
    r = load_receipt()
    require(0 <= (datetime.now(timezone.utc) - datetime.fromisoformat(r['timestamp_utc'])).total_seconds() < 1800)
    from scripts.local_feature_preview import snapshot, digest, schema_summary
    require(digest(snapshot(c)) == r['source_sha256'], 'Preview changed since restore-verified backup')
    from django.db.migrations.executor import MigrationExecutor
    ex = MigrationExecutor(c)
    require([f'{m.app_label}.{m.name}' for m, b in ex.migration_plan(ex.loader.graph.leaf_nodes())] == PENDING)
    from config.local_preview import unlock_connection
    unlock_connection(c)
    from django.core.management import call_command
    start = time.monotonic()
    call_command('migrate', 'support', '0004_policy_evidence_guards', interactive=False, verbosity=0, stdout=io.StringIO())
    seconds = time.monotonic() - start
    after = json.loads(json.dumps(snapshot(c), default=str))
    old = json.loads(Path(r['baseline']).read_text())['snapshot']
    require(set(after['tables']) == set(old['tables']) | {'support_policyrevision', 'support_consentevent'})
    require(all((after['tables'][t] == v for t, v in old['tables'].items() if t not in ('django_migrations', 'auth_permission', 'django_content_type'))))
    require(not MigrationExecutor(c).migration_plan(MigrationExecutor(c).loader.graph.leaf_nodes()))
    for seq,value in old['sequences'].items():
        if seq not in {'django_migrations_id_seq','auth_permission_id_seq','django_content_type_id_seq'}:
            require(after['sequences'][seq]==value,'An old business sequence changed')
    for key in ['columns', 'indexes', 'constraints']:
        require(all((x in after[key] for x in old[key])), 'An old schema definition changed')
    call_command('check', stdout=io.StringIO())
    call_command('migrate', check_unapplied=True, stdout=io.StringIO())
    result = {'status': 'PASS', 'database': 'nau_coffee_test', 'port': 5432, 'migrations': PENDING, 'seconds': round(seconds, 3), 'pending': 0, 'old_business_tables_unchanged': True, 'schema': schema_summary(after)}
    (E / 'migration.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))
    c.close()

def publish():
    c = setup()
    load_receipt()
    from django.db.migrations.executor import MigrationExecutor
    require(not MigrationExecutor(c).migration_plan(MigrationExecutor(c).loader.graph.leaf_nodes()))
    from config.local_preview import unlock_connection, read_profile, write_profile
    unlock_connection(c)
    from django.contrib.auth.models import User, Permission
    previous = json.loads((ROOT / 'docs/qa/2026-11-13-local-cutover/backup-restore-result.json').read_text())
    fixture = json.loads((Path(previous['archive']).parent / 'stage-b-synthetic-fixtures.json').read_text())
    actor = User.objects.get(pk=fixture['admin_id'], is_active=True, is_staff=True)
    require(actor.groups.filter(name='ADMIN').exists() and actor.has_perm('support.change_policy'))
    from support.models import ConsentEvent
    before = ConsentEvent.objects.count()
    from django.test.utils import override_settings
    from support.policy_release import publish_release
    rows = json.loads((ROOT / 'docs/policies/NAU_POLICY_APPROVED_2026-11-17.json').read_text())
    with override_settings(NAU_POLICY_CONSENT_ENABLED=True):
        revisions = publish_release(actor, rows)
    require(ConsentEvent.objects.count() == before, 'Publication must not backfill consent')
    actor.user_permissions.add(Permission.objects.get(content_type__app_label='support', codename='view_consentevent'))
    p = read_profile()
    p.update(policy_enabled=True, features_enabled=True, mode='smoke')
    write_profile(p)
    result = {'status': 'PASS', 'policies': len(revisions), 'policy_date': '2026-11-01', 'versions': [{'slug': r.policy.slug, 'version': r.version, 'published_at': r.published_at.isoformat(), 'hash': r.content_hash} for r in revisions], 'consent_before': before, 'consent_after': ConsentEvent.objects.count(), 'policy_feature': True, 'gate': 'smoke', 'email': 'sandbox', 'audit_permission_actor_id': actor.pk}
    (E / 'publication.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k != 'versions'}))
    c.close()
if __name__ == '__main__':
    E.mkdir(parents=True, exist_ok=True)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['backup', 'migrate', 'publish'])
    args = parser.parse_args()
    try:
        globals()[args.action]()
    except Exception as error:
        import traceback
        print(json.dumps({'status': 'STOP', 'type': type(error).__name__, 'locations': [{'file': Path(f.filename).name, 'line': f.lineno} for f in traceback.extract_tb(error.__traceback__)[-4:]], 'no_automatic_restore': True, 'details': 'Private data/secrets withheld'}))
        raise SystemExit(1) from None
