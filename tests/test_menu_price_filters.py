"""Price-input contract: ASCII nonnegative integers, <12 digits, invalid ignored."""
from django.test import TestCase, override_settings
from catalog.models import Category, Product, ProductVariant, ChannelPrice


@override_settings(NAU_STANDARD_MENU_ENABLED=False)
class MenuPriceFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name='Fixture', slug='fixture')
        for index, price in enumerate((28000, 40000, 49000)):
            product = Product.objects.create(code=f'F{index}', name=f'Fixture {index}',
                                             slug=f'fixture-{index}', category=category)
            variant = ProductVariant.objects.create(product=product, sku=f'FIX-{index}', size='STANDARD', volume_ml=360)
            ChannelPrice.objects.create(variant=variant, channel='WEB', original_price=price)

    def prices(self, params):
        response = self.client.get('/menu/', params)
        self.assertEqual(response.status_code, 200)
        return [p.menu_price_effective for p in response.context['page_obj']]

    def test_valid_bounds_zero_leading_zero_and_length_limit(self):
        self.assertEqual(self.prices({'min_price': '30000', 'max_price': '45000'}), [40000])
        self.assertEqual(self.prices({'min_price': '0', 'max_price': '00040000'}), [28000, 40000])
        self.assertEqual(self.prices({'min_price': '99999999999'}), [])
        self.assertEqual(self.prices({'max_price': '0'}), [])

    def test_invalid_values_are_ignored_for_each_bound(self):
        for key in ('min_price', 'max_price'):
            for value in ('²', '١٢', '１２', '-1', '', '9'*12, '9'*5000,
                          '1 OR 1=1', '1.5', '+1', ' 1 ', '<script>alert(1)</script>'):
                with self.subTest(key=key, value=value[:30]):
                    self.assertEqual(self.prices({key: value}), [28000, 40000, 49000])

    def test_search_sort_and_invalid_bound_preserve_valid_filter(self):
        self.assertEqual(self.prices({'q': 'Fixture', 'min_price': '²',
                                     'max_price': '40000', 'sort': 'price_desc'}), [40000, 28000])
        self.assertEqual(self.prices({'q': 'missing', 'min_price': '²'}), [])
        self.assertEqual(self.prices({'min_price[]': '49000', 'sort': 'injected'}), [28000, 40000, 49000])
        self.assertEqual(self.prices({'min_price': ['49000', '²']}), [28000, 40000, 49000])
