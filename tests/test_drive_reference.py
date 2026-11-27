"""Guard read-only dashboards and functional reference navigation on test fixtures."""
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from commerce.models import StoreSettings, Order
from catalog.models import Product, ChannelPrice


class ReferenceSafetyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.customer = User.objects.create_user('reference-customer')
        cls.customer.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.staff = User.objects.create_user('reference-staff')
        cls.staff.groups.add(Group.objects.get(name='STAFF'))
        cls.admin = User.objects.create_user('reference-admin', is_staff=True)
        cls.admin.groups.add(Group.objects.get(name='ADMIN'))

    def test_configuration_and_management_require_admin_on_get_and_post(self):
        paths = ['/dashboard/settings/security/', '/dashboard/manage/customers/']
        for user in [self.customer, self.staff]:
            self.client.force_login(user)
            for path in paths:
                self.assertEqual(self.client.get(path).status_code, 403)
                self.assertEqual(self.client.post(path, {'is_superuser': '1'}).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(paths[0]).status_code, 302)

    def test_all_six_config_pages_are_read_only_without_creating_defaults(self):
        self.client.force_login(self.admin)
        before = list(StoreSettings.objects.values())
        for section in ['store', 'appearance', 'payment', 'delivery', 'notifications', 'security']:
            path = f'/dashboard/settings/{section}/'
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Chỉ xem cấu hình hiện tại')
            self.assertEqual(self.client.post(path, {'delivery_fee': 1}).status_code, 405)
        self.assertEqual(before, list(StoreSettings.objects.values()))
        self.assertEqual(self.client.get('/dashboard/settings/unknown/').status_code, 404)

    def test_management_filters_and_get_do_not_change_products_or_prices(self):
        self.client.force_login(self.admin)
        before_products = list(Product.objects.values())
        before_prices = list(ChannelPrice.objects.order_by('pk').values())
        for section in ['products', 'categories', 'promotions', 'customers', 'staff']:
            self.assertEqual(self.client.get(f'/dashboard/manage/{section}/').status_code, 200)
        response = self.client.get('/dashboard/manage/products/', {'q': 'CF01', 'active': 'yes'})
        self.assertEqual([p.code for p in response.context['page_obj']], ['CF01'])
        self.assertEqual(before_products, list(Product.objects.values()))
        self.assertEqual(before_prices, list(ChannelPrice.objects.order_by('pk').values()))

    def test_kitchen_guest_customer_denied_staff_can_read_without_creating_orders(self):
        self.assertEqual(self.client.get('/dashboard/kitchen/').status_code, 302)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get('/dashboard/kitchen/').status_code, 403)
        self.client.force_login(self.staff)
        before = Order.objects.count()
        response = self.client.get('/dashboard/kitchen/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Chờ pha chế')
        self.assertEqual(self.client.post('/dashboard/kitchen/').status_code, 405)
        self.assertEqual(Order.objects.count(), before)

    def test_searches_escape_input_and_keep_customer_ownership(self):
        self.client.force_login(self.customer)
        response = self.client.get('/account/orders/', {'q': '<script>', 'status': 'COMPLETED'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['page_obj']), [])
        self.assertNotContains(response, '<script>')
        self.assertContains(response, '&lt;script&gt;')
