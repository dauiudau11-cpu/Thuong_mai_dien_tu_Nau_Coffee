"""Portable initial content provisioning; preview is reserved for guarded cutover."""
import json
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from support.policy_release import publish_release

class Command(BaseCommand):
    help='Publish approved policy content after migrations on an explicitly confirmed fresh/QA environment.'
    def add_arguments(self,p):
        p.add_argument('--actor-id',type=int,required=True);p.add_argument('--confirm-database',required=True)
    def handle(self,*args,**options):
        cfg=connection.settings_dict;name=cfg['NAME']
        if name in ('nau_coffee_test','nau_coffee_dev') or name!=options['confirm_database']:
            raise CommandError('Preview/dev refused here; use the separately approved guarded cutover.')
        if cfg['ENGINE']!='django.db.backends.postgresql':raise CommandError('PostgreSQL required.')
        if name=='nau_coffee_qa_accounts':
            from config.test_runner import verify_qa_identity,unlock_verified_qa
            verify_qa_identity(connection);unlock_verified_qa(connection)
        with connection.cursor() as c:
            c.execute('SELECT current_database(),current_user');identity=c.fetchone()
        if identity!=(name,cfg['USER']):raise CommandError('Actual database/role differs from configuration.')
        executor=MigrationExecutor(connection)
        if executor.migration_plan(executor.loader.graph.leaf_nodes()):raise CommandError('Apply the reviewed migrations before content provisioning.')
        actor=get_user_model().objects.get(pk=options['actor_id'])
        rows=json.loads((Path(settings.BASE_DIR)/'docs/policies/NAU_POLICY_APPROVED_2026-11-17.json').read_text())
        with override_settings(NAU_POLICY_CONSENT_ENABLED=True):result=publish_release(actor,rows)
        self.stdout.write(f'{len(result)} approved policies published; no consent backfill or email.')
