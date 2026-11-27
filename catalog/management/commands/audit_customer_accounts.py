"""Read-only preflight. Never display actual emails, phone numbers or customer names."""
import json
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Count
from django.db.models.functions import Lower, Trim


class Command(BaseCommand):
    help = 'Read-only account conflict counts; no backfill or personal data output.'

    def handle(self, *args, **options):
        with transaction.atomic():
            if connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
            users = get_user_model().objects.all()
            duplicate_groups = users.annotate(normalized=Lower(Trim('email'))).exclude(normalized='').values('normalized').annotate(total=Count('pk')).filter(total__gt=1)
            schema_ready = 'catalog_customerprofile' in connection.introspection.table_names()
            report = {'users': users.count(), 'missing_email': users.filter(email='').count(),
                'case_insensitive_email_conflict_groups': duplicate_groups.count(),
                'profile_schema_present': schema_ready,
                'historical_phone_inference': False, 'writes_performed': False}
            if schema_ready:
                from catalog.customer_models import CustomerProfile
                report['users_without_profile'] = users.filter(customer_profile__isnull=True).count()
                report['profiles_with_email_mirror_mismatch'] = sum(
                    profile.email != profile.user.email.strip().lower()
                    for profile in CustomerProfile.objects.select_related('user').iterator())
            self.stdout.write(json.dumps(report, ensure_ascii=False))
