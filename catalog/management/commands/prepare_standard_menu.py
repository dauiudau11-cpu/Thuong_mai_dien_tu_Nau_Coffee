"""Test-only rehearsal. No supported apply path to development yet."""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from catalog.models import Product, ProductVariant, ChannelPrice, StandardCost
from catalog.approved_menu import MENU
from commerce.operations import check_order_inventory


class Command(BaseCommand):
    help = 'Test only: preview; --apply stages paused SKUs; --cutover retires legacy; --activate requires BOM/stock.'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true')
        parser.add_argument('--activate', action='store_true')
        parser.add_argument('--cutover', action='store_true')

    def handle(self, *args, **options):
        if (options['activate'] or options['cutover']) and not options['apply']:
            raise CommandError('--activate/--cutover requires --apply.')
        config = connection.settings_dict
        from config.test_runner import ACCOUNTS_QA_IDENTITY, LEGACY_TEST_IDENTITY, verify_qa_identity
        identity = (config['NAME'], config['USER'])
        if connection.vendor != 'postgresql' or identity not in (LEGACY_TEST_IDENTITY, ACCOUNTS_QA_IDENTITY):
            raise CommandError('Rehearsal permits only explicit test targets. Development is blocked.')
        if identity == ACCOUNTS_QA_IDENTITY:
            verify_qa_identity(connection)
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')
            if cursor.fetchone() != (*identity, False, False, False):
                raise CommandError('Unsafe actual test identity.')
        try:
            with transaction.atomic():
                products = {p.code: p for p in Product.objects.select_for_update().order_by('pk')}
                if set(products) != {row[0] for row in MENU}:
                    raise CommandError('Unexpected product set; no changes committed.')
                legacy = ProductVariant.objects.exclude(size='FIXED')
                expected = {f'{code}-{size}': (code, size, ml)
                    for code, *_ in MENU for size, ml in
                    ([('STANDARD', 350)] if code in ('CF01', 'CF02', 'CF03') else [('M', 350), ('L', 500)])}
                actual = {v.sku: (v.product.code, v.size, v.volume_ml) for v in legacy.select_related('product')}
                if actual != expected:
                    raise CommandError('Legacy SKU mapping drift; no changes committed.')
                expected_fixed = {f'{code}-{ml}' for code, name, ml, cost, counter, app in MENU}
                if ProductVariant.objects.filter(size='FIXED').exclude(sku__in=expected_fixed).exists():
                    raise CommandError('Unexpected fixed SKU; no changes committed.')
                variants = []
                for code, name, ml, cost, counter, app in MENU:
                    product = products[code]
                    sku = f'{code}-{ml}'
                    variant = ProductVariant.objects.filter(sku=sku).first()
                    if variant and (variant.product_id != product.pk or variant.size != 'FIXED' or variant.volume_ml != ml):
                        raise CommandError('Target SKU conflict; no changes committed.')
                    if not variant and ProductVariant.objects.filter(product=product, size='FIXED').exists():
                        raise CommandError('Fixed size conflict; no changes committed.')
                    if options['apply']:
                        if not variant:
                            variant = ProductVariant.objects.create(product=product, sku=sku, size='FIXED', volume_ml=ml, is_available=False)
                        if (options['cutover'] or options['activate']) and product.name != name:
                            product.name = name
                            product.save(update_fields=['name'])
                    if variant:
                        for channel, amount in [('WEB', counter), ('COUNTER', counter), ('APP', app)]:
                            price = ChannelPrice.objects.filter(variant=variant, channel=channel).first()
                            if price and (price.original_price != amount or price.sale_price is not None):
                                raise CommandError('Target price drift; no changes committed.')
                            if options['apply'] and price is None:
                                ChannelPrice.objects.create(variant=variant, channel=channel, original_price=amount)
                        saved_cost = StandardCost.objects.filter(variant=variant).first()
                        if saved_cost and saved_cost.ingredient_cost != cost:
                            raise CommandError('Target cost drift; no changes committed.')
                        if options['apply'] and saved_cost is None:
                            StandardCost.objects.create(variant=variant, ingredient_cost=cost)
                        variants.append(variant)
                if options['apply']:
                    if options['cutover'] or options['activate']:
                        legacy.update(is_available=False)
                    if options['activate']:
                        check_order_inventory([(variant, 1, []) for variant in variants])
                        ProductVariant.objects.filter(pk__in=[v.pk for v in variants]).update(is_available=True)
        except CommandError:
            raise
        except Exception:
            raise CommandError('Rehearsal failed; transaction rolled back. Details suppressed.') from None
        self.stdout.write('PASS: isolated rehearsal applied; legacy rows retained.' if options['apply'] else 'PASS: preview only; no writes.')
