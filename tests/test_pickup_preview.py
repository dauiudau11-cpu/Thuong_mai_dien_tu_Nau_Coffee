"""The manual preview must fail closed and preserve existing isolated data."""
from types import SimpleNamespace
from unittest.mock import Mock, patch
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from catalog.models import ProductVariant
from commerce.models import Order, StockMovement
from scripts.pickup_preview import guard_preview_database, inspect_preview, prepare_preview, serve_preview, PREVIEW_USERS
from tests.pickup_compatibility_fixture import load_compatibility_fixture, history_state


@override_settings(NAU_STANDARD_MENU_ENABLED=True)
class PickupPreviewSafetyTests(TestCase):
    def test_rejects_dev_configuration_before_any_connection(self):
        db=SimpleNamespace(vendor='postgresql',settings_dict={'ENGINE':'django.db.backends.postgresql',
            'NAME':'nau_coffee_dev','USER':'nau_coffee_app','HOST':'127.0.0.1','TEST':{'NAME':'nau_coffee_dev'}},cursor=Mock())
        with self.assertRaises(ImproperlyConfigured):guard_preview_database(db)
        db.cursor.assert_not_called()

    def test_prepare_uses_anonymized_copy_and_is_idempotent(self):
        from django.contrib.auth.models import User
        self.assertTrue(prepare_preview('Preview-testing-823!'))
        self.assertEqual(ProductVariant.objects.count(),21)
        self.assertEqual(Order.objects.count(),5)
        # Registering a later customer must not collide with synthetic fixture IDs.
        registered=User.objects.create_user(username='preview-new-registration',password='New-customer-testing-823!')
        self.assertNotIn(registered.username,PREVIEW_USERS.values())
        before=history_state();stock=list(StockMovement.objects.order_by('pk').values())
        self.assertFalse(prepare_preview('A-different-password-823!'))
        self.assertEqual(history_state(),before)
        self.assertEqual(stock,list(StockMovement.objects.order_by('pk').values()))
        for role,username in PREVIEW_USERS.items():
            user=User.objects.get(username=username)
            self.assertTrue(user.check_password('Preview-testing-823!'))
            self.assertTrue(user.groups.filter(name=role).exists())

    def test_refuses_to_overwrite_existing_test_data(self):
        load_compatibility_fixture();before=history_state()
        with self.assertRaisesMessage(ImproperlyConfigured,'Refusing overwrite'):
            prepare_preview('Preview-testing-823!')
        self.assertEqual(history_state(),before)

    def test_inspect_is_read_only_and_server_requires_preparation(self):
        self.assertEqual(inspect_preview()['orders'],0)
        self.assertFalse(inspect_preview()['ready'])
        self.assertFalse(Order.objects.exists())
        with patch('django.core.management.call_command') as run:
            with self.assertRaises(ImproperlyConfigured):serve_preview(8001)
            run.assert_not_called()
        prepare_preview('Preview-testing-823!')
        with patch('django.core.management.call_command') as run:
            serve_preview(8001)
            run.assert_called_once_with('runserver','127.0.0.1:8001',use_reloader=False)
