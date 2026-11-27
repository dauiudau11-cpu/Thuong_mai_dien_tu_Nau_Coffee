"""PG17 encrypted backup rehearsal, new QA database only. Never replace an existing DB."""
import hashlib
import json
import os
import re
import secrets
import subprocess
import tempfile
import uuid
from pathlib import Path
from unittest import skipUnless
from django.db import connection
from django.test import TransactionTestCase, override_settings
from django.contrib.auth.models import User
from config.test_runner import verify_qa_identity, ACCOUNTS_QA_IDENTITY
from tests.test_vouchers_v2 import Helpers, SETTINGS, fixture
from commerce import vouchers
from commerce.services import transition_order


@skipUnless(connection.vendor=='postgresql','Requires independently attested PostgreSQL QA')
@override_settings(**SETTINGS)
class QABackupRestoreTests(Helpers,TransactionTestCase):
    def setUp(self):fixture(self.__class__)

    def test_encrypted_backup_restore_to_new_qa_database_preserves_data_and_sequences(self):
        verify_qa_identity(connection)
        self.assertEqual((connection.settings_dict['NAME'],connection.settings_dict['USER']),ACCOUNTS_QA_IDENTITY)
        self.assertFalse(User.objects.exclude(email='').exclude(email__endswith='.invalid').exists())
        public=self.voucher();order=self.place(voucher=public.voucher_id)
        transition_order(self.user,order.public_code,'CANCELLED')
        private=self.voucher('PRIVATE');vouchers.grant_uses(self.admin,private.pk,self.user.pk,2,'Backup fixture')
        self.place(voucher=private.voucher_id)
        legacy=self.voucher();old=legacy.voucher;legacy.delete();self.place(voucher_code=old.code)
        source=ACCOUNTS_QA_IDENTITY[0];role=ACCOUNTS_QA_IDENTITY[1]
        container='nau_localization_qa_20261111'
        target='nau_coffee_qa_accounts_restore_20261112_'+uuid.uuid4().hex[:8]
        self.assertRegex(target,r'^nau_coffee_qa_accounts_restore_20261112_[0-9a-f]{8}$')
        def command(arguments,*,data=None):
            verify_qa_identity(connection)
            result=subprocess.run(arguments,input=data,capture_output=True,timeout=90)
            if result.returncode:raise AssertionError('QA backup/restore command failed; SQL/data/stderr withheld. No automatic cleanup.')
            return result.stdout
        def query(database,statement):
            self.assertIn(database,('postgres',source,target))
            return command(['docker','exec','-i',container,'psql','-X','-qAt','-v','ON_ERROR_STOP=1','-U','postgres','-d',database],data=statement.encode()).decode().strip()
        def fingerprint(database):
            tables=query(database,"BEGIN READ ONLY; SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename; ROLLBACK;").splitlines()
            self.assertTrue(all(re.fullmatch('[a-z0-9_]+',x) for x in tables))
            statements=['BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;']
            for name in tables:statements.append(f"SELECT '{name}',count(*),md5(coalesce(string_agg(md5(row_to_json(t)::text),'' ORDER BY md5(row_to_json(t)::text)),'')) FROM {name} t;")
            statements += ["SELECT sequencename,last_value FROM pg_sequences WHERE schemaname='public' ORDER BY sequencename;",'ROLLBACK;']
            return {'tables':len(tables),'digest':hashlib.sha256(query(database,'\n'.join(statements)).encode()).hexdigest()}
        before=fingerprint(source)
        self.assertEqual(query('postgres',f"BEGIN READ ONLY; SELECT count(*) FROM pg_database WHERE datname='{target}'; ROLLBACK;"),'0')
        dump=command(['docker','exec',container,'pg_dump','-U','postgres','--role',role,'--format=custom',source])
        private_dir=Path(tempfile.mkdtemp(prefix='nau-qa-backup-'));private_dir.chmod(0o700)
        key_dir=Path(tempfile.mkdtemp(prefix='nau-qa-backup-key-'));key_dir.chmod(0o700)
        key=key_dir/'archive.key';key.write_text(secrets.token_urlsafe(64));key.chmod(0o600)
        encrypted=command(['openssl','enc','-aes-256-cbc','-pbkdf2','-salt','-pass','file:'+str(key)],data=dump)
        archive=private_dir/'accounts-qa.dump.enc'
        with os.fdopen(os.open(archive,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:stream.write(encrypted)
        restored=command(['openssl','enc','-d','-aes-256-cbc','-pbkdf2','-pass','file:'+str(key)],data=archive.read_bytes())
        self.assertEqual(hashlib.sha256(restored).digest(),hashlib.sha256(dump).digest())
        query('postgres',f'CREATE DATABASE {target} OWNER postgres TEMPLATE template0;')
        query('postgres',f'REVOKE ALL ON DATABASE {target} FROM PUBLIC; GRANT CONNECT ON DATABASE {target} TO {role};')
        query(target,f'GRANT USAGE, CREATE ON SCHEMA public TO {role};')
        self.assertEqual(query(target,"BEGIN READ ONLY; SELECT count(*) FROM pg_tables WHERE schemaname='public'; ROLLBACK;"),'0')
        command(['docker','exec','-i',container,'pg_restore','-U','postgres','--role',role,'--single-transaction','--exit-on-error','--no-owner','--no-acl','-d',target],data=restored)
        after=fingerprint(target);self.assertEqual(after,before);self.assertEqual(fingerprint(source),before)
        self.assertEqual(query(target,"BEGIN READ ONLY; SELECT count(*) FROM commerce_voucherusev2; ROLLBACK;"),'2')
        self.assertEqual(query(target,"BEGIN READ ONLY; SELECT count(*) FROM commerce_voucherredemption; ROLLBACK;"),'3')
        result={'qa_source':source,'restore_target':target,'container':container,'port':55441,'postgres_major':17,
            'tables':before['tables'],'source_and_restore_tables_rows_sequences_equal':True,'source_unchanged_during_restore':True,
            'new_usage_count':2,'redemptions_including_legacy':3,'encrypted_archive':str(archive),'key_directory':str(key_dir),
            'archive_sha256':hashlib.sha256(encrypted).hexdigest(),'archive_mode':'0600','directory_mode':'0700','key_mode':'0600',
            'plaintext_dump_written_to_disk':False,'existing_databases_dropped_or_restored':False,'runner_guard_unchanged':True,
            'limitation':'Synthetic QA fixtures only; not a backup or restore of preview/dev. Restore target retained; no drop/cleanup.'}
        output=Path(os.environ.get('NAU_ACCEPTANCE_QA_ROOT','docs/qa/2026-11-12-voucher-acceptance'))
        output.mkdir(parents=True,exist_ok=True);(output/'backup-restore.json').write_text(json.dumps(result,indent=2)+'\n')
