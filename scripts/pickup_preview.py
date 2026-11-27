#!/usr/bin/env python3
"""Local Pickup Only preview, exclusively on the guarded test PostgreSQL database.

Never reads the original .env, migrates, seeds, imports to dev, flushes, deletes,
resets an existing preview or exposes a server outside loopback.
"""
import argparse
import getpass
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
PREVIEW_USERS = {'CUSTOMER': 'pickup-preview-customer', 'STAFF': 'pickup-preview-staff', 'ADMIN': 'pickup-preview-admin'}


def guard_preview_database(db=None):
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured
    from django.db import connection
    from config.test_runner import validate_test_target, ACCOUNTS_QA_IDENTITY, verify_qa_identity
    db = db or connection
    if os.environ.get('DJANGO_SETTINGS_MODULE') != 'config.test_settings' or not settings.NAU_STANDARD_MENU_ENABLED:
        raise ImproperlyConfigured('Preview requires config.test_settings and the approved standard menu.')
    validate_test_target(db.settings_dict, keepdb=True, parallel=1)
    if db.vendor != 'postgresql':
        raise ImproperlyConfigured('Preview requires the isolated PostgreSQL test database.')
    if (db.settings_dict['NAME'], db.settings_dict['USER']) == ACCOUNTS_QA_IDENTITY:
        verify_qa_identity(db)  # Fixture rehearsal only; CLI rejects QA credentials/port.
    with db.cursor() as cursor:
        cursor.execute('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole '
            'FROM pg_roles WHERE rolname=current_user')
        if cursor.fetchone() != (db.settings_dict['NAME'], db.settings_dict['USER'], False, False, False):
            raise ImproperlyConfigured('Unsafe actual database identity; preview refused.')


def preview_ready():
    from django.contrib.auth.models import User
    return User.objects.filter(username__in=PREVIEW_USERS.values()).count() == 3


def prepare_preview(password):
    from django.contrib.auth.models import Group, Permission, User
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ImproperlyConfigured
    from django.db import transaction
    from django.db.migrations.executor import MigrationExecutor
    from django.db import connection
    from catalog.models import Product
    from commerce.models import Order
    guard_preview_database()
    executor = MigrationExecutor(connection)
    if executor.migration_plan(executor.loader.graph.leaf_nodes()):
        raise ImproperlyConfigured('Test schema has pending migrations. Run guarded regression first; preview does not migrate.')
    with transaction.atomic():
        if preview_ready():
            return False  # Preserve all existing QA orders, stock and passwords.
        if Product.objects.exists() or Order.objects.exists() or User.objects.exists():
            raise ImproperlyConfigured('Test DB is not empty and has no complete preview. Refusing overwrite; no data was deleted.')
        validate_password(password)
        from tests.pickup_compatibility_fixture import load_compatibility_fixture
        load_compatibility_fixture()
        for role, username in PREVIEW_USERS.items():
            user = User.objects.create_user(username=username, password=password, is_staff=role == 'ADMIN')
            user.groups.add(Group.objects.get(name=role))
        Group.objects.get(name='ADMIN').permissions.add(*Permission.objects.all())
    return True


def inspect_preview():
    from catalog.models import ProductVariant
    from commerce.models import Ingredient, Order, RecipeLine
    guard_preview_database()
    from django.db import connection
    return {'database': connection.settings_dict['NAME'], 'role': connection.settings_dict['USER'], 'ready': preview_ready(),
        'standard_skus': ProductVariant.objects.filter(size='FIXED').count(),
        'ingredients': Ingredient.objects.count(), 'bom_lines': RecipeLine.objects.count(), 'orders': Order.objects.count()}


def serve_preview(port):
    from django.core.exceptions import ImproperlyConfigured
    from django.core.management import call_command
    guard_preview_database()
    if not preview_ready():
        raise ImproperlyConfigured('Prepare the isolated preview first; server not started.')
    if not 1024 <= port <= 65535:
        raise ImproperlyConfigured('Choose a local port from 1024 to 65535.')
    call_command('runserver', f'127.0.0.1:{port}', use_reloader=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['inspect', 'prepare', 'serve'])
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    sys.dont_write_bytecode = True
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.test_settings'
    os.environ['NAU_STANDARD_MENU_ENABLED'] = 'True'
    import django
    django.setup()
    guard_preview_database()
    if args.action == 'prepare':
        if preview_ready():
            print('Existing isolated preview preserved; passwords and data unchanged.')
        else:
            password = getpass.getpass('Mật khẩu DEMO cho ba tài khoản preview (không hiển thị): ')
            confirmation = getpass.getpass('Nhập lại mật khẩu: ')
            if password != confirmation:
                raise SystemExit('Passwords do not match; no preview data written.')
            prepare_preview(password)
            print('Anonymized preview prepared in nau_coffee_test. No dev connection used.')
        for role, username in PREVIEW_USERS.items():
            print(f'{role}: {username}')
    print(inspect_preview())
    if args.action == 'serve':
        print('Local test preview only. Stop this server before running regression on the same test DB.')
        serve_preview(args.port)


if __name__ == '__main__':
    main()
