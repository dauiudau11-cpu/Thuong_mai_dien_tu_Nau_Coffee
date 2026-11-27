from unittest.mock import MagicMock
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from catalog.management.commands.seed_demo import validate_seed_target


class SeedSafetyTests(SimpleTestCase):
    def db(self, name='nau_coffee_dev', user='nau_coffee_app'):
        db = MagicMock()
        db.vendor = 'postgresql'
        db.settings_dict = {'NAME': name, 'USER': user, 'HOST': '127.0.0.1', 'PORT': 5432}
        db.cursor.return_value.__enter__.return_value.fetchone.return_value = (name, user)
        return db

    def test_safe_dev_identity_is_read_only_validated(self):
        db = self.db()
        validate_seed_target(db)
        db.cursor.return_value.__enter__.return_value.execute.assert_called_once_with(
            'SELECT current_database(), current_user')

    def test_old_db_and_wrong_role_are_rejected_before_connection(self):
        for name, user in [('old_database', 'nau_coffee_app'), ('nau_coffee_dev', 'postgres'),
                           ('nau_coffee_test', 'nau_coffee_app')]:
            db = self.db(name, user)
            with self.assertRaises(CommandError):
                validate_seed_target(db)
            db.cursor.assert_not_called()

    def test_actual_connection_mismatch_stops_before_writes(self):
        db = self.db()
        db.cursor.return_value.__enter__.return_value.fetchone.return_value = ('old_database', 'postgres')
        with self.assertRaises(CommandError):
            validate_seed_target(db)

    def test_isolated_test_port_supported_but_dev_port_stays_fixed(self):
        db=self.db('nau_coffee_test','nau_coffee_test_runner')
        db.settings_dict.update(ENGINE='django.db.backends.postgresql',TEST={'NAME':'nau_coffee_test'},PORT=55439)
        validate_seed_target(db)
        dev=self.db();dev.settings_dict['PORT']=55439
        with self.assertRaises(CommandError):validate_seed_target(dev)
        dev.cursor.assert_not_called()
