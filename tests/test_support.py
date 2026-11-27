from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.test import TestCase, Client
from django.urls import reverse
from commerce.models import Order, OrderItem
from catalog.models import ProductVariant
from catalog.customer_models import CustomerProfile
from support.models import Message, Review
from support.services import submit_review
import uuid


class SupportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.buyer = User.objects.create_user('review-buyer')
        cls.other = User.objects.create_user('review-other')
        cls.variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        cls.product = cls.variant.product
        cls.order = Order.objects.create(user=cls.buyer, fulfillment='PICKUP', customer_name='DEMO',
            phone='0900000000', subtotal=30000, total=30000, status='COMPLETED', idempotency_key=uuid.uuid4())
        cls.item = OrderItem.objects.create(order=cls.order, variant=cls.variant, product_name=cls.product.name,
            sku=cls.variant.sku, quantity=1, unit_price=30000, line_total=30000)

    def setUp(self):
        cache.clear()

    def message(self, **extra):
        return {'name': 'Khách DEMO', 'email': 'demo@example.test', 'subject': 'Lời nhắn', 'body': 'Nội dung thử nghiệm', **extra}

    def test_contact_feedback_store_and_post_redirect(self):
        for path, kind in [('/contact/', 'CONTACT'), ('/feedback/', 'FEEDBACK')]:
            self.assertEqual(self.client.post(path, self.message()).status_code, 302)
            self.assertTrue(Message.objects.filter(kind=kind).exists())

    def test_validation_honeypot_and_rate_limit(self):
        self.client.post('/contact/', self.message(email='bad'))
        self.client.post('/contact/', self.message(website='spam.test'))
        self.assertFalse(Message.objects.exists())
        for _ in range(7):
            self.client.post('/contact/', self.message())
        self.assertEqual(Message.objects.count(), 5)

    def test_feedback_order_is_owned_and_requires_login(self):
        self.client.post('/feedback/', self.message(order_code=self.order.public_code))
        self.assertFalse(Message.objects.exists())
        self.client.force_login(self.other)
        self.client.post('/feedback/', self.message(order_code=self.order.public_code))
        self.assertFalse(Message.objects.exists())
        self.client.force_login(self.buyer)
        self.client.post('/feedback/', self.message(order_code=self.order.public_code))
        self.assertEqual(Message.objects.get().order_id, self.order.pk)

    def test_csrf_protected_for_message_and_review(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post('/contact/', self.message()).status_code, 403)
        client.force_login(self.buyer)
        self.assertEqual(client.post(reverse('review', args=[self.product.slug]), {}).status_code, 403)

    def test_review_requires_completed_owned_item_and_matches_product(self):
        data = {'item': self.item.pk, 'rating': 5, 'body': 'Ly cà phê DEMO'}
        with self.assertRaises(ValidationError):
            submit_review(self.other, self.product, data)
        self.order.status = 'CONFIRMED'
        self.order.save()
        with self.assertRaises(ValidationError):
            submit_review(self.buyer, self.product, data)
        self.order.status = 'COMPLETED'
        self.order.save()
        other_product = ProductVariant.objects.get(sku='CF01-STANDARD').product
        with self.assertRaises(ValidationError):
            submit_review(self.buyer, other_product, data)

    def test_review_pending_moderation_unique_and_escaped(self):
        data = {'item': self.item.pk, 'rating': 5, 'body': '<script>alert(1)</script>'}
        review = submit_review(self.buyer, self.product, data)
        url = reverse('product', args=[self.product.slug])
        self.assertNotContains(self.client.get(url), 'alert(1)')
        with self.assertRaises(ValidationError):
            submit_review(self.buyer, self.product, data)
        review.status = 'APPROVED'
        review.save()
        self.assertContains(self.client.get(url), '&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(self.client.get(url), '<script>alert(1)</script>')

    def test_rating_validation_and_eligible_form(self):
        with self.assertRaises(ValidationError):
            submit_review(self.buyer, self.product, {'item': self.item.pk, 'rating': 6, 'body': 'DEMO review'})
        self.client.force_login(self.buyer)
        response = self.client.get(reverse('product', args=[self.product.slug]))
        self.assertContains(response, 'Gửi đánh giá')

    def test_policies_map_label_and_fallback(self):
        for slug in ['returns', 'warranty', 'shipping', 'privacy', 'terms', 'loyalty']:
            self.assertContains(self.client.get('/policies/' + slug + '/'), 'THÔNG TIN CHÍNH SÁCH')
        self.assertEqual(self.client.get('/policies/no-such-policy/').status_code, 404)
        response = self.client.get('/contact/')
        self.assertContains(response, 'maps.app.goo.gl/dhm5y4VkBiPHFYJY9')
        self.assertContains(response, '457/9 Điện Biên Phủ')
        self.assertContains(response, '<iframe')

    def test_round_two_about_footer_navigation_and_partner_branding(self):
        response = self.client.get('/ve-nau/')
        self.assertEqual(response.status_code, 200)
        for text in ['Một chút Nâu, gần bạn hơn.', 'Câu chuyện của Nâu',
                     'Điều Nâu luôn trân trọng', 'Một chút Nâu cho hôm nay']:
            self.assertContains(response, text)
        for index in range(1, 5):
            self.assertContains(response, f'catalog/about/0{index}-')
        for domain in ['tiktok.com/', 'instagram.com/', 'facebook.com/']:
            self.assertContains(response, domain)
        home = self.client.get('/')
        self.assertContains(home, 'href="/ve-nau/">Về Nâu</a>')
        desktop_nav = home.content.decode().split('<nav class="desktop-nav"', 1)[1].split('</nav>', 1)[0]
        self.assertNotIn('/contact/', desktop_nav)
        self.assertNotContains(home, '>Chính sách &amp; Điều khoản</a>')
        self.assertContains(home, '<strong>Địa chỉ:</strong>')
        self.assertContains(home, '<strong>Liên hệ:</strong>')
        self.assertContains(home, '<strong>Email:</strong>')
        partners = self.client.get('/delivery-partners/')
        for brand in ['GrabFood', 'ShopeeFood', 'beFood']:
            self.assertContains(partners, f'alt="Logo {brand}"')

    def test_customer_map_is_not_loaded_for_staff_or_admin(self):
        self.assertContains(self.client.get('/menu/'), '<iframe')
        for role, superuser in [('STAFF', False), ('ADMIN', True)]:
            user = User.objects.create_user(f'map-{role.lower()}', is_staff=True,
                                            is_superuser=superuser)
            user.groups.add(Group.objects.get(name=role))
            self.client.force_login(user)
            response = self.client.get('/menu/')
            self.assertNotContains(response, '<iframe')
            self.assertNotContains(response, 'footer-map')

    def test_contact_prefills_profile_without_mutating_it_and_uses_approved_copy(self):
        customer = User.objects.create_user('contact-profile', email='fallback@example.invalid')
        customer.groups.add(Group.objects.get(name='CUSTOMER'))
        profile = CustomerProfile.objects.create(user=customer, full_name='Khách Nâu',
            phone='+84901234567', email='khach.nau@example.invalid', origin='PUBLIC')
        before = CustomerProfile.objects.values().get(pk=profile.pk)
        self.client.force_login(customer)
        response = self.client.get('/contact/')
        self.assertEqual(response.context['form']['name'].value(), 'Khách Nâu')
        self.assertEqual(response.context['form']['email'].value(), 'khach.nau@example.invalid')
        self.assertContains(response, 'Xem Chính sách &amp; Điều khoản của Nâu Coffee')
        self.assertEqual(before, CustomerProfile.objects.values().get(pk=profile.pk))
        response = self.client.post('/contact/', self.message(name='Tên chỉnh sửa'))
        self.assertRedirects(response, '/contact/')
        self.assertEqual(before, CustomerProfile.objects.values().get(pk=profile.pk))

    def test_admin_only_moderation_and_support_data(self):
        staff = User.objects.create_user('support-staff', is_staff=True)
        staff.groups.add(Group.objects.get(name='STAFF'))
        self.client.force_login(staff)
        self.assertEqual(self.client.get('/admin/support/message/').status_code, 302)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get('/admin/support/review/').status_code, 302)
