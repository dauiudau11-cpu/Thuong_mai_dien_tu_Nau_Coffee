import io

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase

from catalog.models import ProductVariant
from commerce.models import CartItem


class PostPR6UIFixTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', stdout=io.StringIO())
        cls.customer = User.objects.create_user('post-pr6-customer')
        cls.customer.groups.add(Group.objects.get(name='CUSTOMER'))
        cls.variant = ProductVariant.objects.get(sku='CF02-STANDARD')

    def test_promotions_renders_guest_invitation_and_customer_vouchers(self):
        guest = self.client.get('/promotions/')
        self.assertEqual(guest.status_code, 200)
        self.assertContains(guest, 'Đăng nhập để xem voucher của bạn')
        self.assertNotContains(guest, 'voucher-filters')
        self.client.force_login(self.customer)
        customer = self.client.get('/promotions/')
        self.assertEqual(customer.status_code, 200)
        self.assertContains(customer, 'voucher-filters')
        self.assertNotContains(customer, 'Đăng nhập để xem voucher của bạn')

    def test_guest_and_customer_cart_badge_hides_zero_counts_and_caps_over_99(self):
        empty = self.client.get('/menu/')
        self.assertNotContains(empty, 'cart-quantity-badge')
        self.client.post('/cart/add/', {'variant': self.variant.pk, 'quantity': 99})
        other = ProductVariant.objects.get(sku='CF01-STANDARD')
        self.client.post('/cart/add/', {'variant': other.pk, 'quantity': 1})
        guest = self.client.get('/menu/')
        self.assertContains(guest, 'cart-quantity-badge')
        self.assertContains(guest, '99+')
        self.client.force_login(self.customer)
        self.client.get('/cart/')
        customer = self.client.get('/menu/')
        self.assertContains(customer, '99+')
        self.assertEqual(CartItem.objects.filter(cart__user=self.customer).count(), 2)

    def test_checkout_copy_and_product_notice(self):
        self.client.force_login(self.customer)
        self.client.post('/cart/add/', {'variant': self.variant.pk, 'quantity': 1})
        checkout = self.client.get('/checkout/')
        self.assertContains(checkout, 'Thời gian nhận món')
        self.assertContains(checkout, '(Không bắt buộc)')
        self.assertContains(checkout, 'Vui lòng chọn thời gian nhận món từ 07:30 đến 22:00. Đơn đặt trong ngày được tiếp nhận đến 21:30.')
        product = self.client.get('/products/ca-phe-sua-da/')
        self.assertNotContains(product, 'Giá và nguyên liệu được kiểm tra lại khi đặt hàng.')
