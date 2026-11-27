from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from catalog.models import Category, Product, ProductVariant, ChannelPrice


def validate_seed_target(db, sqlite_fallback=False):
    if db.vendor == 'sqlite' and sqlite_fallback and (
            db.settings_dict['NAME'] == ':memory:'
            or str(db.settings_dict['NAME']).startswith('file:memorydb_')):
        return
    config = db.settings_dict
    from config.test_runner import ACCOUNTS_QA_IDENTITY, verify_qa_identity
    if (config.get('NAME'), config.get('USER')) == ACCOUNTS_QA_IDENTITY:
        verify_qa_identity(db)
        return
    expected = {'nau_coffee_dev': 'nau_coffee_app', 'nau_coffee_test': 'nau_coffee_test_runner'}
    name, role = config.get('NAME'), config.get('USER')
    # A separately hosted QA cluster may use a different local port. Dev remains fixed.
    test_port = name == 'nau_coffee_test' and role == 'nau_coffee_test_runner'
    if test_port:
        from config.test_runner import validate_test_target
        from django.core.exceptions import ImproperlyConfigured
        try:
            validate_test_target(config, keepdb=True, parallel=1)
        except ImproperlyConfigured as exc:
            raise CommandError('Refusing unsafe isolated test target.') from exc
    if (db.vendor != 'postgresql' or name not in expected or role != expected[name]
            or config.get('HOST') != '127.0.0.1' or (not test_port and str(config.get('PORT')) != '5432')):
        raise CommandError('Refusing seed: target must be a dedicated Nau database with its own role.')
    with db.cursor() as cursor:
        cursor.execute('SELECT current_database(), current_user')
        if cursor.fetchone() != (name, role):
            raise CommandError('Refusing seed: actual database identity differs from expected target.')


class Command(BaseCommand):
    help = 'Idempotent demo catalog and role setup; never creates passwords or users.'

    @transaction.atomic
    def handle(self, *args, **options):
        validate_seed_target(connection, sqlite_fallback=settings.TEST_SQLITE)
        for name in ['CUSTOMER', 'STAFF', 'ADMIN']:
            group, _ = Group.objects.get_or_create(name=name)
            if name == 'ADMIN':
                # Add missing permissions without removing any existing assignments.
                group.permissions.add(*Permission.objects.all())
        rows = [
            ('CF01', 'Cà phê đen đá', 'ca-phe-den-da', 'Cà phê', 25000, 30000),
            ('CF02', 'Cà phê sữa đá', 'ca-phe-sua-da', 'Cà phê', 30000, 35000),
            ('CF03', 'Bạc xỉu', 'bac-xiu', 'Cà phê', 33000, 39000),
            ('CF04', 'Cold Brew', 'cold-brew', 'Cà phê', 40000, 47000),
            ('TE01', 'Trà đào', 'tra-dao', 'Trà', 25000, 42000),
            ('TE02', 'Trà chanh', 'tra-chanh', 'Trà', 27000, 32000),
            ('OT01', 'Matcha Latte', 'matcha-latte', 'Khác', 45000, 52000),
            ('OT02', 'Cacao sữa đá', 'cacao-sua-da', 'Khác', 39000, 45000),
        ]
        category_slugs = {'Cà phê': 'ca-phe', 'Trà': 'tra', 'Khác': 'khac'}
        for index, (code, name, slug, category_name, web, app) in enumerate(rows):
            category, _ = Category.objects.get_or_create(slug=category_slugs[category_name], defaults={'name': category_name})
            product, _ = Product.objects.get_or_create(code=code, defaults={
                'name': name, 'slug': slug, 'category': category,
                'description': 'Đồ uống và mức giá minh họa cho đồ án Nâu Coffee.',
                'is_featured': index < 4})
            sizes = ['STANDARD'] if index < 3 else ['M', 'L']
            for size in sizes:
                variant, _ = ProductVariant.objects.get_or_create(sku=f'{code}-{size}',
                    defaults={'product': product, 'size': size, 'volume_ml': 500 if size == 'L' else 350})
                delta = 5000 if size == 'L' else 0
                for channel, price in [('WEB', web), ('COUNTER', web), ('APP', app)]:
                    ChannelPrice.objects.get_or_create(variant=variant, channel=channel,
                        defaults={'original_price': price + delta})
        from commerce.models import Ingredient, RecipeLine, OptionRecipeLine, StockMovement, StoreSettings
        from catalog.models import ProductOption
        from support.models import Policy
        from support.views import POLICIES
        for slug, (title, body) in POLICIES.items():
            Policy.objects.get_or_create(slug=slug, defaults={'title': title, 'body': body})
        StoreSettings.objects.get_or_create(name='DEMO')
        cup, _ = Ingredient.objects.get_or_create(sku='DEMO-CUP', defaults={
            'name': 'Ly DEMO', 'unit': 'piece', 'low_stock_threshold': 20})
        water, _ = Ingredient.objects.get_or_create(sku='DEMO-WATER', defaults={
            'name': 'Nước DEMO', 'unit': 'ml', 'low_stock_threshold': 1000})
        for ingredient, stock in [(cup, 1000), (water, 1000000)]:
            StockMovement.objects.get_or_create(idempotency_key=f'seed:{ingredient.sku}', defaults={
                'ingredient': ingredient, 'delta': stock, 'reason': 'PURCHASE', 'note': 'Tồn đầu DEMO, không phải nhập kho thật'})
        for code, *_ in rows:
            mix, _ = Ingredient.objects.get_or_create(sku=f'DEMO-{code}', defaults={
                'name': f'Hỗn hợp minh họa {code}', 'unit': 'g', 'low_stock_threshold': 200})
            StockMovement.objects.get_or_create(idempotency_key=f'seed:{mix.sku}', defaults={
                'ingredient': mix, 'delta': 100000, 'reason': 'PURCHASE', 'note': 'Tồn đầu DEMO; công thức không dùng kinh doanh'})
            for variant in ProductVariant.objects.filter(product__code=code):
                for ingredient, quantity in [(cup, 1), (water, 200 if variant.size == 'L' else 150),
                                              (mix, 30 if variant.size == 'L' else 20)]:
                    RecipeLine.objects.get_or_create(variant=variant, ingredient=ingredient, defaults={'quantity': quantity})
            product = Product.objects.get(code=code)
            for kind, name in [('SUGAR', 'Ít đường'), ('SUGAR', 'Đường tiêu chuẩn'),
                               ('ICE', 'Ít đá'), ('ICE', 'Đá tiêu chuẩn')]:
                ProductOption.objects.get_or_create(product=product, kind=kind, name=name)
            topping, _ = ProductOption.objects.get_or_create(product=product, kind='TOPPING',
                name='Thạch DEMO', defaults={'price_delta': 5000})
            jelly, _ = Ingredient.objects.get_or_create(sku='DEMO-JELLY', defaults={
                'name': 'Thạch minh họa', 'unit': 'g', 'low_stock_threshold': 200})
            StockMovement.objects.get_or_create(idempotency_key='seed:DEMO-JELLY', defaults={
                'ingredient': jelly, 'delta': 100000, 'reason': 'PURCHASE', 'note': 'Tồn đầu topping DEMO'})
            OptionRecipeLine.objects.get_or_create(option=topping, ingredient=jelly, defaults={'quantity': 20})
        self.stdout.write(self.style.SUCCESS('DEMO: seeded 8 products, 13 SKUs and illustrative BOM; existing values preserved.'))
