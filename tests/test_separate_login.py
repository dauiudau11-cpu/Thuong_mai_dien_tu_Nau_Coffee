from django.contrib.auth.models import Group, User
from django.test import Client, TestCase

from catalog.permissions import effective_role


class SeparateLoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        for name in ('CUSTOMER', 'STAFF', 'ADMIN'):
            Group.objects.get_or_create(name=name)
        cls.customer = User.objects.create_user('gateway-customer', password='Gateway-pass-729!')
        cls.customer.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.staff = User.objects.create_user('gateway-staff', password='Gateway-pass-729!')
        cls.staff.groups.add(Group.objects.get(name='STAFF'))
        cls.admin = User.objects.create_user('gateway-admin', password='Gateway-pass-729!', is_staff=True)
        cls.admin.groups.add(Group.objects.get(name='ADMIN'))
        cls.superuser = User.objects.create_superuser('gateway-root', 'root@example.test', 'Gateway-pass-729!')

    def login(self, path, user, next_value=''):
        return self.client.post(path, {'username':user.username, 'password':'Gateway-pass-729!',
            'next':next_value})

    def test_customer_gateway_accepts_only_pure_customer_and_safe_next(self):
        self.assertRedirects(self.login('/accounts/login/', self.customer, '/menu/?q=tra'), '/menu/?q=tra',
            fetch_redirect_response=False)
        self.client.logout()
        response = self.login('/accounts/login/', self.customer, 'https://evil.example/steal')
        self.assertRedirects(response, '/menu/', fetch_redirect_response=False)
        for internal in (self.staff, self.admin, self.superuser):
            self.client.logout()
            response = self.login('/accounts/login/', internal)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Không thể đăng nhập tại cổng này')
            self.assertNotIn('_auth_user_id', self.client.session)

    def test_internal_gateway_routes_staff_admin_and_rejects_customer(self):
        self.assertRedirects(self.login('/internal/login/', self.staff), '/dashboard/kitchen/',
            fetch_redirect_response=False)
        self.client.logout()
        self.assertRedirects(self.login('/internal/login/', self.admin), '/dashboard/',
            fetch_redirect_response=False)
        self.client.logout()
        self.assertRedirects(self.login('/internal/login/', self.superuser), '/dashboard/',
            fetch_redirect_response=False)
        self.client.logout()
        response = self.login('/internal/login/', self.customer)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Không thể đăng nhập tại cổng này')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_precedence_inactive_and_internal_login_page_is_isolated(self):
        mixed = User.objects.create_user('gateway-mixed', password='Gateway-pass-729!')
        mixed.groups.add(Group.objects.get(name='CUSTOMER'), Group.objects.get(name='STAFF'))
        self.assertEqual(effective_role(mixed), 'STAFF')
        self.assertEqual(self.login('/accounts/login/', mixed).status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.login('/internal/login/', mixed), '/dashboard/kitchen/',
            fetch_redirect_response=False)
        inactive = User.objects.create_user('gateway-inactive', password='Gateway-pass-729!', is_active=False)
        inactive.groups.add(Group.objects.get(name='STAFF'))
        self.client.logout()
        self.assertEqual(self.login('/internal/login/', inactive).status_code, 200)
        page = self.client.get('/internal/login/')
        self.assertContains(page, 'Nâu Coffee | Đăng nhập nội bộ')
        self.assertContains(page, 'Hệ thống quản lý và điều hành Nâu Coffee')
        self.assertNotContains(page, 'Tạo tài khoản khách hàng')
        self.assertNotContains(page, 'footer-map')

    def test_internal_navigation_session_logout_and_transaction_denial(self):
        self.login('/internal/login/', self.staff)
        self.assertEqual(self.client.get('/dashboard/kitchen/').status_code, 200)
        website = self.client.get('/')
        self.assertContains(website, 'Trở về trang điều hành')
        self.assertNotContains(website, 'aria-label="Giỏ hàng"')
        self.assertEqual(self.client.get('/cart/').status_code, 403)
        self.assertEqual(self.client.get('/checkout/').status_code, 403)
        self.assertEqual(self.client.get('/account/').status_code, 403)
        self.assertRedirects(self.client.post('/accounts/logout/'), '/internal/login/',
            fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_dashboard_uses_internal_login_and_rbac_stays_server_side(self):
        response = self.client.get('/dashboard/')
        self.assertRedirects(response, '/internal/login/?next=/dashboard/', fetch_redirect_response=False)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get('/dashboard/').status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/dashboard/manage/products/').status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/dashboard/').status_code, 200)

    def test_csrf_is_required_on_both_gateways_and_logout(self):
        csrf = Client(enforce_csrf_checks=True)
        self.assertEqual(csrf.post('/accounts/login/', {}).status_code, 403)
        self.assertEqual(csrf.post('/internal/login/', {}).status_code, 403)
        csrf.force_login(self.staff)
        self.assertEqual(csrf.post('/accounts/logout/').status_code, 403)
