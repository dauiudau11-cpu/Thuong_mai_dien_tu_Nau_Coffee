from unittest import TestCase
from unittest.mock import MagicMock, patch
from django.core.exceptions import ImproperlyConfigured
from config.test_runner import NauTestRunner, validate_test_target
from scripts import bootstrap_postgres


class DatabaseSafetyTests(TestCase):
    def target(self):
        return {'ENGINE': 'django.db.backends.postgresql', 'NAME': 'nau_coffee_test',
            'USER': 'nau_coffee_test_runner', 'HOST': '127.0.0.1',
            'TEST': {'NAME': 'nau_coffee_test'}}

    def test_precreated_nocreatedb_target_is_valid(self):
        self.assertEqual(validate_test_target(self.target(), keepdb=True, parallel=1), 'postgresql')
        self.assertEqual(validate_test_target(self.target(), keepdb=True, parallel=0), 'postgresql')

    def test_dev_and_old_database_targets_rejected(self):
        for name in ['nau_coffee_dev', 'postgres', 'old_database', 'test_nau_coffee_dev']:
            with self.subTest(name=name), self.assertRaises(ImproperlyConfigured):
                validate_test_target(dict(self.target(), NAME=name), keepdb=True, parallel=1)

    def test_dev_superuser_roles_and_other_hosts_rejected(self):
        for updates in [{'USER': 'nau_coffee_app'}, {'USER': 'postgres'}, {'HOST': 'remote'},
                        {'TEST': {'NAME': 'nau_coffee_dev'}}]:
            with self.subTest(updates=updates), self.assertRaises(ImproperlyConfigured):
                validate_test_target(dict(self.target(), **updates), keepdb=True, parallel=1)

    def test_no_keepdb_and_parallel_rejected(self):
        for keepdb, parallel in [(False, 1), (True, 2)]:
            with self.assertRaises(ImproperlyConfigured):
                validate_test_target(self.target(), keepdb=keepdb, parallel=parallel)

    def test_sqlite_only_allows_in_memory(self):
        self.assertEqual(validate_test_target({'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'},
            keepdb=False, parallel=1), 'sqlite')
        with self.assertRaises(ImproperlyConfigured):
            validate_test_target({'ENGINE': 'django.db.backends.sqlite3', 'NAME': 'db.sqlite3'}, keepdb=True, parallel=1)

    @patch('django.db.migrations.executor.MigrationExecutor')
    @patch('config.test_runner.verify_qa_instance')
    @patch('config.test_runner.call_command')
    @patch('config.test_runner.connections')
    def test_runner_uses_existing_verified_schema_without_migration(self, connections, call_command, verify, executor):
        conn = MagicMock()
        conn.vendor = 'postgresql'
        conn.settings_dict = self.target()
        conn.cursor.return_value.__enter__.return_value.fetchone.side_effect = [
            ('nau_coffee_test', 'nau_coffee_test_runner', False, False, False), (17, False, False), (0,)] * 2
        connections.__iter__.return_value = iter(['default'])
        connections.__getitem__.return_value = conn
        executor.return_value.migration_plan.return_value = []
        runner = NauTestRunner(keepdb=True, parallel=1, verbosity=0)
        self.assertEqual(runner.setup_databases(), [])
        runner.teardown_databases([])
        self.assertEqual(verify.call_count, 2)
        call_command.assert_not_called()
        conn.creation.create_test_db.assert_not_called()
        conn.creation.destroy_test_db.assert_not_called()
        self.assertEqual(conn.close.call_count, 2)

    @patch('scripts.bootstrap_postgres.subprocess.run')
    def test_sql_failure_never_exposes_error_or_sql(self, run):
        run.return_value = MagicMock(returncode=1, stderr='password SECRET failure')
        with self.assertRaises(bootstrap_postgres.BootstrapError) as error:
            bootstrap_postgres.sql("CREATE ROLE x PASSWORD 'SECRET'")
        self.assertNotIn('SECRET', str(error.exception))

    def test_env_patterns_ignore_both_credentials_files(self):
        import fnmatch
        patterns = (bootstrap_postgres.ROOT / '.gitignore').read_text().splitlines()
        for filename in ['.env', '.env.test']:
            ignored = False
            for pattern in patterns:
                if fnmatch.fnmatch(filename, pattern.lstrip('!')):
                    ignored = not pattern.startswith('!')
            self.assertTrue(ignored)

    @patch('scripts.bootstrap_postgres.sql')
    @patch('scripts.bootstrap_postgres.subprocess.run')
    def test_docker_permission_failure_creates_nothing(self, run, sql):
        run.return_value = MagicMock(returncode=1)
        with self.assertRaises(bootstrap_postgres.BootstrapError):
            bootstrap_postgres.bootstrap()
        sql.assert_not_called()

    @patch('scripts.bootstrap_postgres.sql')
    @patch('scripts.bootstrap_postgres.subprocess.run')
    def test_partial_failure_reports_created_role_without_cleanup_or_secret(self, run, sql):
        import io
        from contextlib import redirect_stdout
        from pathlib import Path
        from tempfile import TemporaryDirectory
        run.return_value = MagicMock(returncode=0)
        sql.side_effect = ['', '', bootstrap_postgres.BootstrapError('SQL error suppressed')]
        output = io.StringIO()
        with TemporaryDirectory() as directory, patch.object(bootstrap_postgres, 'ROOT', Path(directory)):
            with patch.object(bootstrap_postgres.secrets, 'token_urlsafe', return_value='TEST_SECRET'), redirect_stdout(output):
                with self.assertRaises(bootstrap_postgres.BootstrapError):
                    bootstrap_postgres.bootstrap()
            env_file = Path(directory) / '.env'
            self.assertTrue(env_file.exists())
            self.assertEqual(env_file.stat().st_mode & 0o777, 0o600)
            self.assertIn('role:nau_coffee_app', output.getvalue())
            self.assertIn('create database nau_coffee_dev', output.getvalue())
            self.assertNotIn('TEST_SECRET', output.getvalue())
            self.assertFalse(any('DROP' in call.args[0] for call in sql.call_args_list))

    @patch('scripts.bootstrap_postgres.sql')
    @patch('scripts.bootstrap_postgres.subprocess.run')
    def test_existing_resources_never_modified(self, run, sql):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        run.return_value = MagicMock(returncode=0)
        sql.return_value = 'nau_coffee_dev'
        with TemporaryDirectory() as directory, patch.object(bootstrap_postgres, 'ROOT', Path(directory)):
            with self.assertRaises(SystemExit):
                bootstrap_postgres.bootstrap()
            self.assertEqual(sql.call_count, 1)
            self.assertFalse((Path(directory) / '.env').exists())
