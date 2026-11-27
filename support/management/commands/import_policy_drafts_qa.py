"""Explicit QA-only importer; never publishes or targets preview."""
import json
from pathlib import Path
from django.core.management.base import BaseCommand,CommandError
from django.db import connection,transaction
from django.contrib.auth import get_user_model
from config.test_runner import verify_qa_identity,unlock_verified_qa
from support.models import Policy,PolicyRevision

class Command(BaseCommand):
    help='Import the supplied policy drafts into verified independent QA only; no publication.'
    def add_arguments(self,parser):parser.add_argument('--actor-id',type=int,required=True)
    def handle(self,*args,**options):
        verify_qa_identity(connection)
        if connection.settings_dict['NAME']!='nau_coffee_qa_accounts':raise CommandError('Accounts QA only.')
        unlock_verified_qa(connection)
        actor=get_user_model().objects.get(pk=options['actor_id'])
        from catalog.permissions import has_role
        if not has_role(actor,'ADMIN'):raise CommandError('Admin actor required.')
        from django.conf import settings
        rows=json.loads((Path(settings.BASE_DIR)/'docs/policies/NAU_POLICY_DRAFTS_2026-11-17.json').read_text())
        with transaction.atomic():
            for row in rows:
                policy,_=Policy.objects.get_or_create(slug=row['slug'],defaults={'title':row['title'],'body':row['body'][:10000]})
                PolicyRevision.objects.get_or_create(policy=policy,version=row['version'],defaults={'title':row['title'],'body':row['body'],'created_by':actor})
        self.stdout.write('11 drafts available on QA; no publication or legacy updates.')
