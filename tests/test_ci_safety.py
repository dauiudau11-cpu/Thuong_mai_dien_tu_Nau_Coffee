"""CI bootstrap refuses existing resources; no real databases are touched here."""
import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch
from scripts import prepare_ci_postgres as ci


class CIBootstrapSafetyTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.addCleanup(patch.stopall)
        patch.object(ci, 'ROOT', self.root).start()
        patch.dict(os.environ, {'NAU_CI_LOCAL': '1', 'NAU_CI_POSTGRES_CONTAINER': 'fresh-ci'}, clear=True).start()
        self.run = patch.object(ci.subprocess, 'run').start()

    def response(self, output='', status=0):
        return Mock(returncode=status, stdout=output, stderr='suppressed')

    def preflight(self, identity='postgres|nau_ci_owner|17', databases='postgres\ntemplate0\ntemplate1', roles=''):
        self.run.side_effect = [self.response(identity), self.response(databases), self.response(roles),
            self.response(), self.response(), self.response()]

    def test_refuses_non_ci_context_before_docker(self):
        os.environ.pop('NAU_CI_LOCAL')
        with self.assertRaises(RuntimeError):
            ci.prepare()
        self.run.assert_not_called()

    def test_refuses_existing_files_without_overwrite(self):
        target = self.root / '.env.test'
        target.write_text('existing-placeholder')
        with self.assertRaises(RuntimeError):
            ci.prepare()
        self.assertEqual(target.read_text(), 'existing-placeholder')
        self.run.assert_not_called()

    def test_refuses_inherited_development_database_binding(self):
        os.environ['DATABASE_URL'] = 'not-a-real-binding'
        with self.assertRaises(RuntimeError):
            ci.prepare()
        self.run.assert_not_called()

    def test_refuses_wrong_owner_or_version_before_file_creation(self):
        self.preflight(identity='postgres|nau_cloud_owner|17')
        with self.assertRaises(RuntimeError):
            ci.prepare()
        self.assertEqual(self.run.call_count, 1)
        self.assertFalse((self.root / '.env.test').exists())

    def test_refuses_existing_database_and_role(self):
        for databases, roles in [('postgres\nnau_coffee_dev', ''), ('postgres', 'nau_coffee_test_runner')]:
            self.preflight(databases=databases, roles=roles)
            with self.assertRaises(RuntimeError):
                ci.prepare()
            self.assertFalse((self.root / '.env.test').exists())

    def test_creates_only_test_target_and_never_logs_password(self):
        self.preflight()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            ci.prepare()
        target = self.root / '.env.test'
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        text = target.read_text()
        password = text.split('nau_coffee_test_runner:')[1].split('@')[0]
        self.assertNotIn(password, output.getvalue())
        sql = [call.kwargs['input'] for call in self.run.call_args_list]
        self.assertTrue(any('NOSUPERUSER NOCREATEDB NOCREATEROLE' in query for query in sql))
        self.assertTrue(any('CREATE DATABASE nau_coffee_test ' in query for query in sql))
        self.assertFalse(any('DROP ' in query or 'CREATE DATABASE nau_coffee_dev' in query for query in sql))

    def test_partial_failure_preserves_new_credentials_and_does_no_cleanup(self):
        self.preflight()
        self.run.side_effect = [self.response('postgres|nau_ci_owner|17'), self.response('postgres'),
            self.response(), self.response(status=1)]
        with self.assertRaises(RuntimeError):
            ci.prepare()
        self.assertTrue((self.root / '.env.test').exists())
        self.assertFalse(any('DROP ' in call.kwargs['input'] for call in self.run.call_args_list))
