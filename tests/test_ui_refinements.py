"""Presentation and empty-checkout safety, against the existing pricing service."""
from decimal import Decimal
import re
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase, SimpleTestCase, override_settings
from catalog.templatetags.nau_ui import vnd
from commerce.models import Order, Payment


class CurrencyDisplayTests(SimpleTestCase):
    def test_integer_vnd_grouping_zero_and_large_values(self):
        for value, expected in [(0, '0 đ'), (8250, '8.250 đ'), (1234567, '1.234.567 đ'),
                                (Decimal('43000'), '43.000 đ')]:
            with self.subTest(value=value):
                self.assertEqual(vnd(value), expected)

    def test_invalid_or_fractional_values_are_not_silently_rounded(self):
        for value in [None, '', '<script>', Decimal('1.5'), Decimal('NaN')]:
            with self.subTest(value=value):
                self.assertEqual(vnd(value), '—')


class EmptyCheckoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)
        cls.user = User.objects.create_user('empty-checkout-demo')
        cls.user.groups.add(Group.objects.get(name='CUSTOMER'))

    def test_empty_get_has_menu_link_without_payment_form_or_spurious_error(self):
        self.client.force_login(self.user)
        response = self.client.get('/checkout/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Giỏ hàng đang trống')
        self.assertContains(response, 'href="/menu/"')
        self.assertNotContains(response, 'name="payment_method"')
        self.assertNotContains(response, 'value="place"')
        self.assertFalse(list(response.context['messages']))

    def test_empty_forged_post_cannot_create_order_or_payment(self):
        self.client.force_login(self.user)
        self.client.get('/checkout/')
        response = self.client.post('/checkout/', {'action': 'place', 'total': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        self.assertFalse(Payment.objects.exists())

    def test_guest_still_needs_login_and_customer_cannot_access_operations(self):
        self.assertEqual(self.client.get('/checkout/').status_code, 302)
        self.client.force_login(self.user)
        for path in ['/dashboard/inventory/', '/dashboard/orders/new-manual/', '/dashboard/reports/']:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)


class CustomerPresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_demo', verbosity=0)

    def test_home_and_menu_share_server_price_without_changing_rows(self):
        from catalog.approved_menu import MENU
        from catalog.models import ChannelPrice, ProductVariant
        legacy = ProductVariant.objects.get(sku='CF02-STANDARD')
        approved = next(row for row in MENU if row[0] == 'CF02')
        fixed = ProductVariant.objects.create(product=legacy.product, sku='CF02-360',
            size='FIXED', volume_ml=approved[2], is_available=False)
        for channel, amount in [('WEB', approved[4]), ('COUNTER', approved[4]), ('APP', approved[5])]:
            ChannelPrice.objects.create(variant=fixed, channel=channel, original_price=amount)
        prices = list(ChannelPrice.objects.order_by('pk').values_list('pk', 'original_price', 'sale_price'))
        # Exercise both legacy and fixed projections: the card must use WEB, not APP
        # or the retired SKU. All fixture writes precede the read-only assertion.
        for standard, variant in [(False, legacy), (True, fixed)]:
            expected = variant.prices.get(channel='WEB').current_price
            with self.subTest(sku=variant.sku), override_settings(NAU_STANDARD_MENU_ENABLED=standard):
                for path, price_class in [('/', ' class="home-product-price"'), ('/menu/', '')]:
                    response = self.client.get(path)
                    self.assertEqual(response.status_code, 200)
                    products = response.context['products'] if path == '/' else response.context['page_obj']
                    displayed = next(product for product in products if product.code == 'CF02')
                    self.assertEqual(displayed.menu_price_effective, expected)
                    card = re.search(r'<article\b[^>]*\bbeverage-CF02\b[^>]*>.*?</article>',
                        response.content.decode(), re.S)
                    self.assertIsNotNone(card, path)
                    self.assertInHTML(f'<strong{price_class}>{vnd(expected)}</strong>', card.group())
                    self.assertNotRegex(card.group(), r'\bTừ\s')
                    self.assertIn('/products/ca-phe-sua-da/', card.group())
        self.assertEqual(prices, list(ChannelPrice.objects.order_by('pk').values_list('pk', 'original_price', 'sale_price')))

    def test_menu_removes_duplicate_category_navigation(self):
        response = self.client.get('/menu/', {'q':'Trà', 'min_price':10000, 'sort':'price_desc', 'page':2})
        self.assertNotContains(response,'premium-menu-tabs')
        self.assertNotContains(response,'name="category"')
        self.assertContains(response,'name="min_price"')

    def test_product_preview_uses_backend_option_price_and_posts_same_contract(self):
        from catalog.models import ProductVariant
        variant = ProductVariant.objects.get(sku='CF02-STANDARD')
        response = self.client.get('/products/ca-phe-sua-da/')
        self.assertContains(response, 'data-unit-price="30000"')
        self.assertContains(response, f'name="variant" value="{variant.pk}"')
        self.assertContains(response, 'action="/cart/add/"')
        media = re.search(r'<figure class="product-media">.*?</figure>', response.content.decode(), re.S)
        self.assertIsNotNone(media)
        self.assertIn('<img ', media.group())
        self.assertNotIn('Hình ảnh minh họa.', media.group())
        self.assertNotIn('Ảnh sản phẩm chính thức đang được chuẩn bị', media.group())
