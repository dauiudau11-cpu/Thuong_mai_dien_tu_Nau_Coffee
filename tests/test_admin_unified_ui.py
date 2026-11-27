"""Shared presentation only; no operational rules or Staff permissions are replaced."""
from django.contrib.auth.models import Permission
from django.test import TestCase, Client, override_settings
from tests.test_vouchers_v2 import fixture, Helpers, SETTINGS


@override_settings(**SETTINGS)
class UnifiedAdminTests(Helpers, TestCase):
    @classmethod
    def setUpTestData(cls):
        fixture(cls)
        cls.admin.is_staff=True
        cls.admin.save(update_fields=['is_staff'])
        cls.admin.user_permissions.add(*Permission.objects.all())

    def test_custom_and_native_pages_share_one_shell(self):
        self.client.force_login(self.admin)
        for path in ['/admin/','/dashboard/','/dashboard/vouchers/','/dashboard/manage/products/', '/dashboard/settings/store/','/dashboard/inventory/','/dashboard/orders/new-manual/']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,200,path)
            self.assertContains(response,'id="nav-sidebar"',count=1)
            self.assertContains(response,'id="header"',count=1)
            self.assertNotContains(response,'class="site-header')
            self.assertNotContains(response,'class="premium-ops-layout')
            links=[entry['url'] for group in response.context['nau_admin_groups'] for entry in group['items']]
            self.assertEqual(len(links),len(set(links)))

    def test_native_model_links_keep_permission_checks_and_active_state(self):
        self.client.force_login(self.admin)
        response=self.client.get('/admin/catalog/channelprice/')
        self.assertEqual(response.status_code,200)
        entries=[entry for group in response.context['nau_admin_groups'] for entry in group['items']]
        self.assertTrue(next(e for e in entries if e['url']=='/admin/catalog/channelprice/')['active'])
        self.assertContains(response,'Mã giảm giá / Voucher')

    def test_admin_role_without_native_permission_keeps_custom_access_only(self):
        self.admin.is_staff=False;self.admin.save(update_fields=['is_staff'])
        self.client.force_login(self.admin)
        response=self.client.get('/dashboard/vouchers/')
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.context['nau_admin_native'])
        self.assertEqual(self.client.get('/admin/').status_code,302)

    def test_staff_layout_is_preserved_and_admin_management_denied(self):
        self.client.force_login(self.staff)
        response=self.client.get('/dashboard/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'premium-ops-layout')
        self.assertNotContains(response,'id="nav-sidebar"')
        self.assertEqual(self.client.get('/dashboard/vouchers/').status_code,403)
        self.assertEqual(self.client.get('/dashboard/manage/products/').status_code,403)
        self.assertEqual(self.client.get('/admin/').status_code,302)

    def test_customer_cannot_enter_operations_or_admin(self):
        self.client.force_login(self.user)
        for path in ['/dashboard/','/dashboard/vouchers/','/dashboard/manage/products/']:
            self.assertEqual(self.client.get(path).status_code,403)
        self.assertEqual(self.client.get('/admin/').status_code,302)

    def test_custom_shell_still_enforces_csrf(self):
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.admin)
        self.assertEqual(csrf.post('/dashboard/vouchers/', {'action':'grant'}).status_code,403)
        response=csrf.get('/dashboard/vouchers/')
        self.assertContains(response,'name="csrfmiddlewaretoken"')
        self.assertContains(response,'voucher-live.js')

    @override_settings(NAU_CUSTOMER_ACCOUNTS_ENABLED=False)
    def test_disabled_accounts_have_no_dead_navigation_links(self):
        self.client.force_login(self.admin)
        response=self.client.get('/admin/')
        self.assertNotContains(response,'href="/dashboard/customers/lookup/"')
        self.assertNotContains(response,'href="/dashboard/customers/create/"')

    def test_native_app_index_preserves_contextual_model_directory(self):
        self.client.force_login(self.admin)
        response=self.client.get('/admin/catalog/')
        self.assertEqual(response.status_code,200)
        self.assertContains(response,'id="content-main"')
        self.assertContains(response,'href="/admin/catalog/product/"')
        self.assertNotContains(response,'id="traffic-title"')
        self.assertNotContains(self.client.get('/admin/'),'id="content-main"')
