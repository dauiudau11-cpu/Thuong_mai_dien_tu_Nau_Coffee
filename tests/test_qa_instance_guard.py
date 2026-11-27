"""No database access: assert attestation fails before any writable setup."""
import json
import subprocess
from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.core.exceptions import ImproperlyConfigured
from config.test_runner import NauTestRunner, verify_qa_instance


class QAInstanceGuardTests(TestCase):
    def config(self, port=55441):
        return {'ENGINE': 'django.db.backends.postgresql', 'HOST': '127.0.0.1', 'PORT': port,
                'NAME': 'nau_coffee_test', 'USER': 'nau_coffee_test_runner',
                'TEST': {'NAME': 'nau_coffee_test'}}

    def containers(self):
        return [dict(Name='/nau_localization_qa_20261111', Id='qa', State={'Running': True},
                     NetworkSettings={'Ports': {'5432/tcp': [{'HostIp': '127.0.0.1', 'HostPort': '55441'}]}},
                     Mounts=[{'Source': '/qa-data', 'Destination': '/var/lib/postgresql/data'}]),
                dict(Name='/pg_lab_postgres', Id='preview',
                     Mounts=[{'Source': '/preview-data', 'Destination': '/var/lib/postgresql/data'}])]

    @patch('config.test_runner.subprocess.run')
    def test_preview_or_missing_port_refused_before_docker_or_connection(self, run):
        for port in (5432, '', None, 55442):
            with self.assertRaises(ImproperlyConfigured): verify_qa_instance(self.config(port))
        run.assert_not_called()

    @patch('config.test_runner.subprocess.run')
    def test_verified_separate_cluster_accepted(self, run):
        run.return_value.stdout = json.dumps(self.containers())
        verify_qa_instance(self.config())

    @patch('config.test_runner.subprocess.run')
    def test_missing_docker_or_invalid_metadata_refused(self, run):
        for error in (OSError(), subprocess.TimeoutExpired('docker', 10)):
            run.side_effect = error
            with self.assertRaises(ImproperlyConfigured): verify_qa_instance(self.config())
        run.side_effect = None
        for stdout in ('bad json', '[]', '{}'):
            run.return_value.stdout = stdout
            with self.assertRaises(ImproperlyConfigured): verify_qa_instance(self.config())

    @patch('config.test_runner.subprocess.run')
    def test_shared_data_or_nonloopback_or_stopped_cluster_refused(self, run):
        for case in ('shared', 'nested', 'binding', 'stopped', 'missing_mount'):
            data = self.containers()
            if case == 'shared': data[0]['Mounts'] = data[1]['Mounts']
            if case == 'nested': data[0]['Mounts'][0]['Source'] = '/preview-data/nested'
            if case == 'binding': data[0]['NetworkSettings']['Ports']['5432/tcp'][0]['HostIp'] = '0.0.0.0'
            if case == 'stopped': data[0]['State']['Running'] = False
            if case == 'missing_mount': data[0]['Mounts'] = []
            run.return_value.stdout = json.dumps(data)
            with self.assertRaises(ImproperlyConfigured): verify_qa_instance(self.config())

    @patch('config.test_runner.connections')
    @patch('config.test_runner.call_command')
    def test_runner_refuses_preview_before_connection_or_migration(self, command, connections):
        conn = MagicMock(settings_dict=self.config(5432))
        connections.__iter__.return_value = iter(['default'])
        connections.__getitem__.return_value = conn
        with self.assertRaises(ImproperlyConfigured):
            NauTestRunner(keepdb=True, parallel=1).setup_databases()
        conn.cursor.assert_not_called()
        command.assert_not_called()

    @patch('config.test_runner.connections')
    @patch('config.test_runner.verify_qa_instance')
    @patch('django.db.migrations.executor.MigrationExecutor')
    def test_pending_schema_refused_without_unlock_or_migration(self, executor, verify, connections):
        conn = MagicMock(settings_dict=self.config())
        conn.cursor.return_value.__enter__.return_value.fetchone.side_effect = [
            ('nau_coffee_test', 'nau_coffee_test_runner', False, False, False), (17, False, False), (0,)] * 2
        connections.__iter__.return_value = iter(['default'])
        connections.__getitem__.return_value = conn
        executor.return_value.migration_plan.return_value = ['pending']
        with self.assertRaises(ImproperlyConfigured):
            NauTestRunner(keepdb=True, parallel=1).setup_databases()
        conn.ensure_connection.assert_not_called()
        self.assertNotIn('OPTIONS', conn.settings_dict)

    def test_test_settings_commands_default_to_read_only(self):
        import os
        import sys
        result = subprocess.run([sys.executable, '-B', '-c',
            "import config.test_settings as s; assert s.DATABASES['default']['OPTIONS']['options'] == "
            "'-c default_transaction_read_only=on'"], capture_output=True, text=True,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_preview_launcher_cannot_use_qa_credential_override(self):
        import os
        import sys
        from pathlib import Path
        result = subprocess.run([sys.executable, '-B', '-c',
            "import sys; sys.argv=['scripts/pickup_preview.py','serve']; "
            "import config.test_settings"], capture_output=True, text=True,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                 'NAU_QA_ENV_FILE': str(Path('.env.test').resolve())})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Preview cannot serve or prepare the regression QA instance', result.stderr)


class AccountsQATargetTests(TestCase):
    def target(self):
        return {'ENGINE':'django.db.backends.postgresql','NAME':'nau_coffee_qa_accounts',
                'USER':'nau_coffee_qa_accounts_runner','HOST':'127.0.0.1','PORT':'55441',
                'TEST':{'NAME':'nau_coffee_qa_accounts'}}

    def test_exact_accounts_tuple_is_allowed(self):
        from config.test_runner import validate_test_target
        self.assertEqual(validate_test_target(self.target(),keepdb=True,parallel=1),'postgresql')

    def test_wrong_identity_port_host_and_missing_test_name_fail_closed(self):
        from config.test_runner import validate_test_target
        for change in ({'PORT':'5432'},{'PORT':''},{'HOST':'localhost'}, {'HOST':'remote'},
                       {'NAME':'nau_coffee_test'},{'USER':'nau_coffee_test_runner'},
                       {'NAME':'nau_coffee_dev'},{'USER':'postgres'},{'TEST':{}}):
            with self.subTest(change=change),self.assertRaises(ImproperlyConfigured):
                validate_test_target({**self.target(),**change},keepdb=True,parallel=1)

    @patch('config.test_runner.verify_qa_instance')
    def test_actual_role_mismatch_or_privilege_escalation_is_rejected(self, attest):
        from config.test_runner import verify_qa_identity
        for row in [('nau_coffee_test','nau_coffee_test_runner',False,False,False),
                    ('nau_coffee_qa_accounts','nau_coffee_qa_accounts_runner',True,False,False)]:
            conn=MagicMock(settings_dict=self.target())
            conn.cursor.return_value.__enter__.return_value.fetchone.return_value=row
            with self.assertRaises(ImproperlyConfigured):verify_qa_identity(conn)
            conn.ensure_connection.assert_not_called()

    def test_unsafe_private_file_is_rejected_before_database_connection(self):
        import os,sys,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'.env.qa.accounts';path.write_text('not read')
            path.chmod(0o644)
            result=subprocess.run([sys.executable,'-B','-c','import config.test_settings'],
                env={**os.environ,'NAU_QA_ENV_FILE':str(path),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('mode 0600',result.stderr)
