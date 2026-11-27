from getpass import getpass
import sys
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection, transaction
from .seed_demo import validate_seed_target


class Command(BaseCommand):
    help = 'Preview account creation; --apply prompts for a password locally. No defaults/secrets in arguments.'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--role', choices=['CUSTOMER', 'STAFF', 'ADMIN'], required=True)
        parser.add_argument('--apply', action='store_true')

    def handle(self, *args, **options):
        validate_seed_target(connection, settings.TEST_SQLITE)
        if connection.vendor == 'postgresql' and connection.settings_dict['NAME'] != 'nau_coffee_dev':
            raise CommandError('Demo accounts can only be provisioned in nau_coffee_dev.')
        username, role = options['username'], options['role']
        user = get_user_model()(username=username, is_staff=role == 'ADMIN', is_superuser=False)
        try:
            user.full_clean(exclude=['password'])
        except ValidationError:
            raise CommandError('Invalid or existing username; no user changed.') from None
        group = Group.objects.filter(name=role).first()
        if group is None:
            raise CommandError('Role group missing; no user created.')
        if not options['apply']:
            self.stdout.write(f'PREVIEW: {username} / {role}; is_staff={user.is_staff}, '
                f'is_superuser=False; database=nau_coffee_dev; no writes. Add --apply only after approval.')
            return
        if not sys.stdin.isatty():
            raise CommandError('Use an interactive Ubuntu terminal for hidden password entry; no user created.')
        password = getpass('Mật khẩu (nhập ẩn, không gửi vào chat): ')
        if password != getpass('Nhập lại mật khẩu: '):
            raise CommandError('Passwords do not match; no user created.')
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError(' '.join(error.messages)) from None
        with transaction.atomic():
            user.set_password(password)
            user.save()
            user.groups.add(group)
        self.stdout.write(self.style.SUCCESS(f'Created demo account {username}, role {role}. Password not displayed.'))
