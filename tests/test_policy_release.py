import json
from pathlib import Path
from django.test import TestCase,override_settings
from django.utils import timezone
from django.contrib.auth.models import Permission
from tests.test_vouchers_v2 import fixture,SETTINGS
from support.policy_release import publish_release
from support.models import PolicyRevision,ConsentEvent
from support.policies import active

@override_settings(**dict(SETTINGS,NAU_POLICY_CONSENT_ENABLED=True))
class PolicyReleaseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fixture(cls);cls.admin.user_permissions.add(Permission.objects.get(codename='change_policy'))
    def test_approved_policy_date_is_not_publication_or_consent_time(self):
        rows=json.loads(Path('docs/policies/NAU_POLICY_APPROVED_2026-11-17.json').read_text())
        start=timezone.now();revisions=publish_release(self.admin,rows)
        self.assertEqual(len(active()),11);self.assertFalse(ConsentEvent.objects.exists())
        for r in revisions:
            self.assertEqual(timezone.localtime(r.effective_at).date().isoformat(),'2026-11-01')
            self.assertGreaterEqual(r.published_at,start)
            self.assertGreaterEqual(r.created_at,start)
        before=list(PolicyRevision.objects.values_list('pk','published_at','content_hash'))
        publish_release(self.admin,rows);self.assertEqual(list(PolicyRevision.objects.values_list('pk','published_at','content_hash')),before)
        privacy=self.client.get('/policies/privacy/');self.assertContains(privacy,'01/11/2026');self.assertContains(privacy,'Công bố')
        for term in ['PostgreSQL','DJANGO_','5432','backup/','schema','credentials']:
            self.assertNotContains(privacy,term)
