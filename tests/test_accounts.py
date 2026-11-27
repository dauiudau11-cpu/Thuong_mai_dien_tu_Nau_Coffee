from django.contrib.auth.models import Group, User
from django.test import TestCase, Client
from catalog.models import Address
from support.models import Policy
from unittest.mock import patch


class AccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('profile-buyer', password='Testing-profile-732!')
        customer_group, _ = Group.objects.get_or_create(name='CUSTOMER')
        self.user.groups.add(customer_group)
        self.other = User.objects.create_user('profile-other')
        self.address = Address.objects.create(user=self.other, label='Riêng tư', recipient='DEMO', phone='0900000000', text='Địa chỉ DEMO khác')
        self.client.force_login(self.user)

    def test_profile_whitelists_fields_and_password_change(self):
        self.client.post('/account/profile/', {'first_name': 'Tên DEMO', 'last_name': 'Khách',
            'email': 'demo@example.test', 'is_staff': True, 'is_superuser': True})
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Tên DEMO')
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        response = self.client.post('/account/password/', {'old_password': 'Testing-profile-732!',
            'new_password1': 'Changed-testing-profile-821!', 'new_password2': 'Changed-testing-profile-821!'})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('Changed-testing-profile-821!'))

    def test_address_create_edit_delete_owner_only_and_csrf(self):
        data = {'label': 'Nhà DEMO', 'recipient': 'DEMO', 'phone': '0900000000', 'text': 'Địa chỉ thử nghiệm', 'user': self.other.pk}
        self.assertEqual(self.client.post('/account/addresses/', data).status_code, 302)
        own = Address.objects.get(user=self.user)
        self.assertNotContains(self.client.get('/account/addresses/'), 'Địa chỉ DEMO khác')
        self.assertEqual(self.client.post(f'/account/addresses/{self.address.pk}/edit/', data).status_code, 404)
        self.assertEqual(self.client.post(f'/account/addresses/{self.address.pk}/remove/').status_code, 404)
        self.assertEqual(self.client.get(f'/account/addresses/{own.pk}/remove/').status_code, 405)
        guarded = Client(enforce_csrf_checks=True)
        guarded.force_login(self.user)
        self.assertEqual(guarded.post(f'/account/addresses/{own.pk}/remove/').status_code, 403)
        self.client.post(f'/account/addresses/{own.pk}/remove/')
        self.assertFalse(Address.objects.filter(pk=own.pk).exists())

    def test_pickup_checkout_does_not_accept_saved_addresses(self):
        from commerce.forms import CheckoutForm
        form = CheckoutForm({'saved_address': self.address.pk}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertNotIn('saved_address', form.fields)
        self.assertNotIn('saved_address', form.cleaned_data)

    @patch('support.services.time.time', return_value=1792254000)
    def test_login_and_signup_throttle(self, clock):
        self.client.logout()
        for _ in range(15):
            self.client.post('/accounts/login/', {'username': 'invalid-demo', 'password': 'wrong'})
        self.assertEqual(self.client.post('/accounts/login/', {'username': self.user.username,
            'password': 'Testing-profile-732!'}).status_code, 429)
        for _ in range(10):
            self.client.post('/accounts/register/', {'username': ''})
        self.assertEqual(self.client.post('/accounts/register/', {'username': ''}).status_code, 429)

    def test_policy_admin_content_is_rendered_safely(self):
        Policy.objects.create(slug='returns', title='Đổi trả DEMO', body='<script>unsafe</script>')
        self.assertContains(self.client.get('/policies/returns/'), '&lt;script&gt;unsafe&lt;/script&gt;')
