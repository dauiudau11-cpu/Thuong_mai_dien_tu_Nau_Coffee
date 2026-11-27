from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from support.models import SubmissionLimit


class Command(BaseCommand):
    help = 'Remove expired anti-spam counters only; no customer content or orders.'

    def handle(self, *args, **options):
        count, _ = SubmissionLimit.objects.filter(created_at__lt=timezone.now()-timedelta(days=1)).delete()
        self.stdout.write(f'Pruned {count} expired rate-limit counters.')
