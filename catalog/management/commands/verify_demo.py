from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from catalog.models import Category, Product, ProductVariant, ChannelPrice
from .seed_demo import validate_seed_target
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Read-only verification of demo catalog counts, relationships and duplicates.'

    def handle(self, *args, **options):
        validate_seed_target(connection, settings.TEST_SQLITE)
        codes = ['CF01', 'CF02', 'CF03', 'CF04', 'TE01', 'TE02', 'OT01', 'OT02']
        products = Product.objects.filter(code__in=codes)
        variants = ProductVariant.objects.filter(product__in=products)
        prices = ChannelPrice.objects.filter(variant__in=variants)
        if (products.count(), variants.count(), prices.count()) != (8, 13, 39):
            raise CommandError('Unexpected demo catalog counts.')
        for product in products:
            expected = 1 if product.code in codes[:3] else 2
            if product.variants.count() != expected:
                raise CommandError('Unexpected variant relationship.')
        for variant in variants:
            if set(variant.prices.values_list('channel', flat=True)) != {'WEB', 'COUNTER', 'APP'}:
                raise CommandError('Missing or duplicate channel price.')
        for queryset, fields in [(products, ['code']), (variants, ['sku']), (prices, ['variant_id', 'channel'])]:
            if queryset.values(*fields).annotate(n=Count('pk')).filter(n__gt=1).exists():
                raise CommandError('Duplicate demo data found.')
        if Group.objects.filter(name__in=['CUSTOMER', 'STAFF', 'ADMIN']).count() != 3:
            raise CommandError('Demo roles missing.')
        self.stdout.write(self.style.SUCCESS('PASS: 8 demo products / 13 SKUs / 39 channel prices / 3 roles; valid relations, no duplicates.'))
