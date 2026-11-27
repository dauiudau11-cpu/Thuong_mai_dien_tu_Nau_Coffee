"""Admin voucher navigation and shared legacy-data explanation."""
from django.test import TestCase, override_settings
from tests.test_vouchers_v2 import Helpers, fixture, SETTINGS


@override_settings(**SETTINGS)
class VoucherNavigationTests(Helpers, TestCase):
    @classmethod
    def setUpTestData(cls):
        fixture(cls)
        cls.admin.is_staff = True
        cls.admin.save(update_fields=["is_staff"])
        from django.contrib.auth.models import Permission
        cls.admin.user_permissions.add(*Permission.objects.filter(content_type__app_label="commerce", content_type__model="voucher"))

    def test_admin_can_follow_voucher_navigation_and_legacy_links(self):
        self.client.force_login(self.admin)
        for path in ['/admin/', '/dashboard/vouchers/', '/admin/commerce/voucher/', '/admin/commerce/voucher/add/']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, '/admin/commerce/voucher/')
            self.assertContains(response, 'Mã giảm giá / Voucher')
        for path in ['/dashboard/vouchers/', '/admin/commerce/voucher/']:
            self.assertContains(self.client.get(path), 'Chính sách trước đây')

    def test_customer_staff_cannot_manage_or_grant(self):
        for user in [self.user, self.staff]:
            self.client.force_login(user)
            self.assertEqual(self.client.get('/dashboard/vouchers/').status_code, 403)
            for path in ['/admin/', '/admin/commerce/voucher/', '/admin/commerce/voucher/add/']:
                response = self.client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn('/admin/login/', response.url)
            self.assertEqual(self.client.post('/dashboard/vouchers/', {'action': 'grant'}).status_code, 403)

    @override_settings(NAU_VOUCHERS_V2_ENABLED=False)
    def test_disabled_feature_has_no_admin_link(self):
        self.client.force_login(self.admin)
        self.assertNotContains(self.client.get('/admin/'), 'href="/dashboard/vouchers/"')

    def test_home_preserves_groups_recent_actions_and_shared_sidebar(self):
        self.client.force_login(self.admin)
        response = self.client.get('/admin/')
        self.assertContains(response, 'id="recent-actions-module"')
        self.assertContains(response, 'id="nav-sidebar"', count=1)
        self.assertContains(response, 'class="breadcrumbs"')
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, 'aria-controls="nav-sidebar"')
        self.assertContains(response, 'Mã giảm giá / Voucher')
        self.assertContains(response, 'TỔNG QUAN')
