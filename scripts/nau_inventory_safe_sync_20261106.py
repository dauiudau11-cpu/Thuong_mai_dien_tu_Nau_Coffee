#!/usr/bin/env python3
"""Nâu Coffee V3: controlled internal trial inventory and recipe importer.

This script never seeds the old menu, changes pricing, activates a SKU, or edits
an existing order. Run --preview before --apply. Meant for the isolated WSL
Django project with the approved 8 FIXED variants already cut over.
"""
import argparse
import os
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

INGREDIENTS = (
    ('NL01', 'Cốt cà phê', 'ml', 200_000),
    ('NL02', 'Cà phê ủ lạnh', 'ml', 400_000),
    ('NL03', 'Cốt trà', 'ml', 750_000),
    ('NL04', 'Nước lọc', 'ml', 800_000),
    ('NL05', 'Sữa tươi', 'ml', 1_000_000),
    ('NL06', 'Sữa đặc', 'ml', 150_000),
    ('NL07', 'Siro đào', 'ml', 60_000),
    ('NL08', 'Đào miếng', 'g', 120_000),
    ('NL09', 'Nước cốt chanh', 'ml', 40_000),
    ('NL10', 'Siro đường', 'ml', 120_000),
    ('NL11', 'Bột matcha', 'g', 10_000),
    ('NL12', 'Bột cacao', 'g', 35_000),
    ('NL13', 'Đá viên', 'g', 2_500_000),
    ('NL14', 'Ly đựng', 'piece', 12_000),
    ('NL15', 'Nắp ly', 'piece', 12_000),
)

# Integer quantities per drink, units as specified by INGREDIENTS.
RECIPES = {
    'CF01-360': {'NL01': 65, 'NL04': 130, 'NL13': 160, 'NL14': 1, 'NL15': 1},
    'CF02-360': {'NL01': 55, 'NL06': 35, 'NL04': 90, 'NL13': 160, 'NL14': 1, 'NL15': 1},
    'CF03-360': {'NL01': 30, 'NL05': 120, 'NL06': 35, 'NL13': 150, 'NL14': 1, 'NL15': 1},
    'CF04-500': {'NL02': 280, 'NL04': 50, 'NL13': 180, 'NL14': 1, 'NL15': 1},
    'TE01-700': {'NL03': 250, 'NL07': 40, 'NL08': 80, 'NL04': 90, 'NL13': 260, 'NL14': 1, 'NL15': 1},
    'TE02-700': {'NL03': 270, 'NL09': 25, 'NL10': 40, 'NL04': 80, 'NL13': 270, 'NL14': 1, 'NL15': 1},
    'OT01-700': {'NL11': 7, 'NL05': 300, 'NL10': 35, 'NL04': 60, 'NL13': 260, 'NL14': 1, 'NL15': 1},
    'OT02-700': {'NL12': 22, 'NL05': 280, 'NL06': 35, 'NL04': 80, 'NL13': 250, 'NL14': 1, 'NL15': 1},
}

# Audit note is intentionally concise. Do not display it to customers.
AUDIT_NOTE = 'Dữ liệu kiểm thử nội bộ'
APPLY_ACK = 'CHAP_NHAN_GHI_KHO_KIEM_THU'


def check_plan():
    codes = {sku for sku, *_ in INGREDIENTS}
    if len(codes) != len(INGREDIENTS) or set(RECIPES) != {
        'CF01-360', 'CF02-360', 'CF03-360', 'CF04-500',
        'TE01-700', 'TE02-700', 'OT01-700', 'OT02-700',
    }:
        raise RuntimeError('STOP: Bộ dữ liệu có mã trùng hoặc thiếu SKU.')
    needs = defaultdict(int)
    for sku, recipe in RECIPES.items():
        if not recipe or not set(recipe) <= codes or any(value <= 0 for value in recipe.values()):
            raise RuntimeError('STOP: BOM không hợp lệ: ' + sku)
        for key, amount in recipe.items():
            needs[key] += amount * 1000
    for key, _, unit, available in INGREDIENTS:
        if unit not in ('g', 'ml', 'piece') or available < needs[key]:
            raise RuntimeError('STOP: Tồn kho không đủ cho kế hoạch 1.000 ly/món: ' + key)
    return needs


def main():
    parser = argparse.ArgumentParser(description='Nâu Coffee: preview/apply BOM & inventory trial data')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--preview', action='store_true', help='Chỉ đọc database, không ghi')
    group.add_argument('--apply', action='store_true', help='Ghi 15 ingredients, 50 BOM lines, 15 stock movements')
    parser.add_argument('--approve', default='', help='Mã xác nhận bắt buộc khi --apply')
    parser.add_argument('--backup', type=Path, help='Bản backup PostgreSQL mới nhất; bắt buộc khi --apply')
    args = parser.parse_args()

    if args.apply and args.approve != APPLY_ACK:
        parser.error('--apply cần --approve ' + APPLY_ACK)
    if args.apply and not args.backup:
        parser.error('--apply bắt buộc --backup <đường_dẫn_dump>')
    if args.apply:
        p = args.backup.expanduser().resolve(strict=True)
        trusted_dir = (Path.home() / 'naucoffee-backups').resolve()
        if not p.is_file() or p.suffix != '.dump' or p.parent != trusted_dir or p.stat().st_size == 0:
            parser.error('Backup không tồn tại, rỗng hoặc không ở thư mục backup riêng.')
        print('BACKUP FILE:', p.name)
        print('Lưu ý: cần kiểm tra pg_restore --list và hash backup trước khi ghi.')

    check_plan()
    if os.getenv('NAU_ENV_FILE', '.env') != '.env':
        raise SystemExit('STOP: Không được dùng file môi trường khác .env cho thao tác này.')
    if os.getenv('DJANGO_SETTINGS_MODULE', 'config.settings') != 'config.settings':
        raise SystemExit('STOP: Chỉ hỗ trợ config.settings trong dự án phát triển.')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    import django
    django.setup()
    from django.conf import settings
    from django.db import connection, transaction
    from catalog.approved_menu import MENU
    from catalog.models import ChannelPrice, Product, ProductVariant, StandardCost
    from commerce.models import (Ingredient, OptionRecipeLine, RecipeLine,
                                 StockMovement, Order, OrderItem, Payment)

    if connection.vendor != 'postgresql':
        raise SystemExit('STOP: Chỉ hỗ trợ PostgreSQL.')
    with transaction.atomic():
        with connection.cursor() as cursor:
            if args.preview:
                cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('SELECT current_database(), current_user')
            actual = cursor.fetchone()
            if actual != ('nau_coffee_dev', 'nau_coffee_app'):
                raise SystemExit('STOP: Không đúng database phát triển / tài khoản hạn chế: ' + str(actual))

        if not settings.NAU_STANDARD_MENU_ENABLED:
            raise SystemExit('STOP: Menu chuẩn chưa được bật trong Django settings.')
        # Lock existing variant rows on apply, to serialize with catalog edits.
        product_qs = Product.objects.order_by('code')
        variant_qs = ProductVariant.objects.order_by('sku').select_related('product')
        if args.apply:
            product_qs = product_qs.select_for_update()
            variant_qs = variant_qs.select_for_update()
        products = list(product_qs)
        variants = list(variant_qs)

        expected_names = {code: name for code, name, ml, cost, web, app in MENU}
        expected_skus = {f'{code}-{ml}': (code, ml, cost, web, app)
                         for code, name, ml, cost, web, app in MENU}
        if len(products) != 8 or {p.code: p.name for p in products} != expected_names:
            raise SystemExit('STOP: Sản phẩm/ tên menu khác bảng đã duyệt.')
        if len(variants) != 21 or sum(v.size == 'FIXED' for v in variants) != 8:
            raise SystemExit('STOP: Cần đúng 21 SKU, gồm 8 SKU chuẩn.')
        fixed = {v.sku: v for v in variants if v.size == 'FIXED'}
        if set(fixed) != set(expected_skus) or any(v.is_available for v in variants):
            raise SystemExit('STOP: SKU không khớp hoặc đã có SKU mở bán.')
        for sku, (code, ml, cost, web, app) in expected_skus.items():
            v = fixed[sku]
            if v.product.code != code or v.volume_ml != ml:
                raise SystemExit('STOP: Sai ánh xạ SKU ' + sku)
            prices = list(ChannelPrice.objects.filter(variant=v))
            observed = {p.channel: p.original_price for p in prices}
            if observed != {'WEB': web, 'COUNTER': web, 'APP': app} or len(prices) != 3:
                raise SystemExit('STOP: Giá SKU không khớp ' + sku)
            if any(p.sale_price is not None for p in prices):
                raise SystemExit('STOP: Có sale không được duyệt ' + sku)
            if not StandardCost.objects.filter(variant=v, ingredient_cost=cost).exists():
                raise SystemExit('STOP: Thiếu cost chuẩn: ' + sku)

        # Fail closed for any existing inventory data, not just conflicting SKU names.
        before = {
            'Ingredient': Ingredient.objects.count(),
            'RecipeLine': RecipeLine.objects.count(),
            'OptionRecipeLine': OptionRecipeLine.objects.count(),
            'StockMovement': StockMovement.objects.count(),
        }
        if any(before.values()):
            raise SystemExit('STOP: Đã có nguyên liệu/BOM/giao dịch kho; không tự thêm hoặc ghi đè: ' + str(before))
        original_orders = (Order.objects.count(), OrderItem.objects.count(), Payment.objects.count())
        print('DATABASE: nau_coffee_dev')
        print('FIXED SKU: 8 PAUSED / LEGACY SKU: 13 PAUSED')
        print('CURRENT INVENTORY:', before)
        print('PLAN: 15 INGREDIENTS; 50 RECIPE LINES; 15 INITIAL STOCK MOVEMENTS')
        print('PLAN: CAPACITY >= 1000 DRINKS PER MENU ITEM')
        print('HISTORICAL ORDERS:', original_orders)

        if args.apply:
            ing_by_code = {}
            for code, name, unit, stock in INGREDIENTS:
                ingredient = Ingredient.objects.create(
                    sku=code, name=name, unit=unit,
                    low_stock_threshold=Decimal(stock) / Decimal(20), is_active=True,
                )
                ing_by_code[code] = ingredient
            for sku, recipe in RECIPES.items():
                for ingredient_code, amount in recipe.items():
                    RecipeLine.objects.create(
                        variant=fixed[sku], ingredient=ing_by_code[ingredient_code],
                        quantity=Decimal(amount),
                    )
            for code, name, unit, stock in INGREDIENTS:
                StockMovement.objects.create(
                    ingredient=ing_by_code[code],
                    delta=Decimal(stock), reason='ADJUST',
                    note=AUDIT_NOTE, actor=None,
                    idempotency_key=f'nau:v3:trial-stock-initial:{code}',
                )
            after = (Ingredient.objects.count(), RecipeLine.objects.count(), StockMovement.objects.count())
            if after != (15, 50, 15):
                raise RuntimeError('STOP: Số bản ghi mới sai, transaction sẽ rollback: ' + str(after))
            if original_orders != (Order.objects.count(), OrderItem.objects.count(), Payment.objects.count()):
                raise RuntimeError('STOP: Biến động đơn lịch sử, transaction sẽ rollback.')
            if ProductVariant.objects.filter(is_available=True).exists():
                raise RuntimeError('STOP: Có SKU bị bật bán ngoài dự kiến.')
            print('PASS: ATOMIC INVENTORY IMPORT: 15 INGREDIENTS, 50 BOM LINES, 15 MOVEMENTS')
            print('PASS: LEGACY SKU, PRICES, ORDERS UNCHANGED BY THIS COMMAND')
            print('SKU ACTIVATION: NOT PERFORMED')
        else:
            print('PASS: PREVIEW ONLY. NO DATABASE WRITES')


if __name__ == '__main__':
    main()
