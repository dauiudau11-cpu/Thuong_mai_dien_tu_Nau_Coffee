from django.test import TestCase, override_settings

from catalog.models import Category, ChannelPrice, Product, ProductVariant


@override_settings(NAU_STANDARD_MENU_ENABLED=False)
class MenuSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        coffee = Category.objects.create(name='Cà phê', slug='ca-phe')
        other = Category.objects.create(name='Khác', slug='khac')
        cls._add('CF01', 'Cà phê sữa', coffee, 39000)
        cls._add('CF02', 'Bạc xỉu', coffee, 35000)
        cls._add('OT01', 'Cacao sữa', other, 49000)
        cls._add('OT02', 'Matcha sữa', other, 45000)
        cls._add('OFF', 'Cà phê ẩn', coffee, 10000, active=False)
        cls._add('APP', 'Cà phê APP', coffee, 10000, channel='APP')

    @classmethod
    def _add(cls, code, name, category, price, active=True, channel='WEB'):
        product = Product.objects.create(
            code=code, name=name, slug=code.lower(), category=category, is_active=active,
        )
        variant = ProductVariant.objects.create(
            product=product, sku=f'{code}-FIXED', size='FIXED', volume_ml=360,
        )
        ChannelPrice.objects.create(variant=variant, channel=channel, original_price=price)

    def names(self, **params):
        response = self.client.get('/menu/', params)
        self.assertEqual(response.status_code, 200)
        return response, [product.name for product in response.context['page_obj']]

    def test_exact_partial_case_accentless_and_whitespace_search(self):
        cases = {
            'Cà phê sữa': ['Cà phê sữa'],
            'CÀ PHÊ': ['Cà phê sữa'],
            '  ca phe sua  ': ['Cà phê sữa'],
            'bac': ['Bạc xỉu'],
            'bac xiu': ['Bạc xỉu'],
            'ca cao': ['Cacao sữa'],
        }
        for query, expected in cases.items():
            with self.subTest(query=query):
                self.assertEqual(self.names(q=query)[1], expected)

    def test_search_combines_with_category_and_sort(self):
        self.assertEqual(
            self.names(q='sua', category='khac', sort='name_desc')[1],
            ['Matcha sữa', 'Cacao sữa'],
        )
        self.assertEqual(
            self.names(q='sua', category='khac', sort='price_asc')[1],
            ['Matcha sữa', 'Cacao sữa'],
        )

    def test_empty_result_copy_and_clear_link_preserve_filters(self):
        response, names = self.names(q='khong-co', category='ca-phe', sort='name_desc')
        self.assertEqual(names, [])
        self.assertContains(response, 'Không tìm thấy thức uống phù hợp.')
        self.assertContains(response, 'Vui lòng thử từ khóa khác.')
        self.assertContains(response, 'category=ca-phe')
        self.assertNotContains(response, 'q=khong-co')

    def test_only_active_products_with_active_category_and_web_price_are_returned(self):
        self.assertEqual(self.names(q='ca phe')[1], ['Cà phê sữa'])

    def test_name_desc_mapping(self):
        self.assertEqual(
            self.names(category='ca-phe', sort='name_desc')[1],
            ['Cà phê sữa', 'Bạc xỉu'],
        )
