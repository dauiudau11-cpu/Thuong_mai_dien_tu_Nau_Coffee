from datetime import timedelta
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.forms import modelform_factory
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.utils import timezone
from catalog.models import Category, Product, ProductVariant, ChannelPrice, ProductImage


class FoundationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_seed_is_idempotent_and_preserves_admin_edits(self):
        price = ChannelPrice.objects.first()
        price.original_price = 12345
        price.save()
        call_command('seed_demo', verbosity=0)
        self.assertEqual(Product.objects.count(), 8)
        self.assertEqual(ProductVariant.objects.count(), 13)
        self.assertEqual(ChannelPrice.objects.count(), 39)
        price.refresh_from_db()
        self.assertEqual(price.original_price, 12345)

    def test_public_pages_render(self):
        for url in ['/', '/menu/', '/products/matcha-latte/', '/accounts/login/', '/accounts/register/', '/healthz/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)
        self.assertContains(self.client.get('/products/matcha-latte/'), 'catalog/premium/ot01.webp')

    def test_combined_filters_sort_and_empty_state(self):
        response = self.client.get('/menu/', {'q': 'Trà', 'category': 'tra', 'min_price': 25000,
            'max_price': 30000, 'sort': 'price_desc'})
        self.assertEqual([p.code for p in response.context['page_obj']], ['TE02', 'TE01'])
        empty = self.client.get('/menu/?q=missing')
        self.assertEqual(empty.context['page_obj'].paginator.count, 0)
        self.assertEqual(list(empty.context['page_obj']), [])
        self.assertContains(empty, '<h2>Chưa tìm thấy món phù hợp</h2>', html=True)
        self.assertContains(empty, '<a class="button" href="/menu/">Xóa bộ lọc</a>', html=True)
        self.assertNotContains(empty, 'class="product-card ')

    def test_sale_window_is_used_for_filter_and_display(self):
        price = ChannelPrice.objects.get(variant__sku='CF01-STANDARD', channel='WEB')
        now = timezone.now()
        price.sale_price = 20000
        price.sale_starts_at = now - timedelta(days=1)
        price.sale_ends_at = now + timedelta(days=1)
        price.save()
        self.assertEqual(price.current_price, 20000)
        self.assertContains(self.client.get('/products/ca-phe-den-da/'), '<del>25.000 đ</del>', html=True)
        response = self.client.get('/menu/?max_price=21000')
        self.assertEqual([p.code for p in response.context['page_obj']], ['CF01'])
        price.sale_ends_at = now - timedelta(seconds=1)
        price.save()
        self.assertEqual(price.current_price, 25000)

    def test_invalid_sale_is_rejected_by_database(self):
        price = ChannelPrice.objects.first()
        with self.assertRaises(IntegrityError), transaction.atomic():
            price.sale_price = price.original_price + 1
            price.save()

    def test_inactive_category_and_variant_are_hidden(self):
        Category.objects.filter(slug='tra').update(is_active=False)
        self.assertEqual(self.client.get('/products/tra-dao/').status_code, 404)
        ProductVariant.objects.filter(product__code='CF01').update(is_available=False)
        self.assertNotContains(self.client.get('/menu/'), 'Cà phê đen đá')

    def test_registration_hashes_password_and_cannot_choose_role(self):
        response = self.client.post('/accounts/register/', {'username': 'customer',
            'password1': 'Example-test-pass-829!', 'password2': 'Example-test-pass-829!', 'role': 'ADMIN'})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='customer')
        self.assertTrue(user.check_password('Example-test-pass-829!'))
        self.assertFalse(user.is_staff)
        self.assertEqual(list(user.groups.values_list('name', flat=True)), ['CUSTOMER'])

    def test_role_gate_does_not_trust_is_staff_flag(self):
        user = User.objects.create_user('staff-flag', is_staff=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get('/dashboard/').status_code, 403)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        user.groups.add(Group.objects.get(name='STAFF'))
        self.assertEqual(self.client.get('/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        user.groups.add(Group.objects.get(name='ADMIN'))
        self.assertEqual(self.client.get('/admin/').status_code, 200)

    def test_logout_requires_post_and_private_page_relocks(self):
        user = User.objects.create_user('auth-user', password='Example-test-pass-829!')
        user.groups.add(Group.objects.get(name='CUSTOMER'))
        self.client.login(username=user.username, password='Example-test-pass-829!')
        self.assertEqual(self.client.get('/account/').status_code, 200)
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.client.post('/accounts/logout/')
        self.assertEqual(self.client.get('/account/').status_code, 302)

    def test_csrf_and_escaping(self):
        self.assertEqual(Client(enforce_csrf_checks=True).post('/accounts/register/', {}).status_code, 403)
        response = self.client.get('/menu/', {'q': '<script>alert(1)</script>', 'sort': 'DROP TABLE'})
        self.assertNotContains(response, '<script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_login_next_cannot_redirect_offsite(self):
        user = User.objects.create_user('redirect-user', password='Example-test-pass-829!')
        user.groups.add(Group.objects.get(name='CUSTOMER'))
        response = self.client.post('/accounts/login/', {'username': 'redirect-user',
            'password': 'Example-test-pass-829!', 'next': 'https://evil.example/'})
        self.assertRedirects(response, '/menu/')

    def test_upload_rejects_content_disguised_as_image(self):
        form_class = modelform_factory(ProductImage, fields=['product', 'image', 'alt'])
        form = form_class(data={'product': Product.objects.first().pk, 'alt': 'demo'},
            files={'image': SimpleUploadedFile('fake.png', b'<script>alert(1)</script>', content_type='image/png')})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
