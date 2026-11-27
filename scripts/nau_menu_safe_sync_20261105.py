#!/usr/bin/env python3
"""Nau Coffee V3: guarded standard-menu stage and cutover on local dev DB.

Uses catalog.approved_menu.MENU as the sole price/volume/cost source.
Never resets, seeds, migrates, commits, pushes, or modifies orders, carts, BOM,
stock, existing SKU prices, or the environment file.

Run from the NauCoffee repo root with its virtualenv Python.
Preview is read-only; --stage and --cutover require a verified backup file.
"""
from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

from django.core.management.base import CommandError


def main() -> None:
    parser = argparse.ArgumentParser(description="Safe Nâu Coffee approved-menu sync")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preview", action="store_true", help="Read-only, no writes")
    modes.add_argument("--stage", action="store_true", help="Create eight paused SKUs, 24 prices, eight costs")
    modes.add_argument("--cutover", action="store_true", help="Retire 13 old SKUs; keep 8 new SKUs paused")
    parser.add_argument("--backup", type=Path, help="Existing private PostgreSQL .dump, required for writes")
    args = parser.parse_args()

    root = Path.cwd().resolve()
    if not (root / "manage.py").is_file() or not (root / "catalog/approved_menu.py").is_file():
        parser.error("Run from ~/projects/NauCoffee, not another folder")
    if os.getenv("NAU_ENV_FILE", ".env") != ".env":
        parser.error("NAU_ENV_FILE must be .env")
    if os.getenv("DJANGO_SETTINGS_MODULE", "config.settings") != "config.settings":
        parser.error("DJANGO_SETTINGS_MODULE must be config.settings")
    sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    import django
    django.setup()
    from django.conf import settings
    from django.db import connection, transaction
    from catalog.approved_menu import MENU
    from catalog.models import Product, ProductVariant, ChannelPrice, StandardCost

    if Path(settings.BASE_DIR).resolve() != root or settings.TEST_SQLITE:
        raise CommandError("Unsafe settings or repository path")
    cfg = connection.settings_dict
    if (connection.vendor != "postgresql" or str(cfg.get("NAME")) != "nau_coffee_dev"
            or str(cfg.get("USER")) != "nau_coffee_app"
            or str(cfg.get("HOST")) != "127.0.0.1" or str(cfg.get("PORT")) != "5432"):
        raise CommandError("STOP: Expected PostgreSQL nau_coffee_dev/nau_coffee_app on 127.0.0.1:5432")
    with connection.cursor() as cur:
        cur.execute("""SELECT current_database(), current_user, r.rolsuper, r.rolcreatedb, r.rolcreaterole
                       FROM pg_roles r WHERE r.rolname = current_user""")
        actual = cur.fetchone()
    if actual != ("nau_coffee_dev", "nau_coffee_app", False, False, False):
        raise CommandError(f"STOP: Unexpected actual DB identity: {actual}")

    approved_codes = {row[0] for row in MENU}
    if len(MENU) != 8 or len(approved_codes) != 8:
        raise CommandError("STOP: Approved menu is not eight unique products")

    if args.stage or args.cutover:
        if args.backup is None:
            raise CommandError("STOP: --backup PATH required for changes")
        backup = args.backup.expanduser().resolve()
        private_dir = (Path.home() / "naucoffee-backups").resolve()
        if (backup.parent != private_dir or not backup.name.startswith("nau_coffee_dev_")
                or backup.suffix != ".dump" or not backup.is_file()
                or backup.stat().st_size < 1024
                or backup.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO)):
            raise CommandError("STOP: Missing, insecure, or unexpected private database backup")

    legacy_specs = {
        f"{code}-{size}": (code, size, volume)
        for code, *_ in MENU
        for size, volume in (
            (("STANDARD", 350),) if code in {"CF01", "CF02", "CF03"} else (("M", 350), ("L", 500))
        )
    }
    legacy_old_names = {
        "CF01": "Cà phê đen đá", "CF02": "Cà phê sữa đá",
        "OT01": "Matcha Latte", "OT02": "Cacao sữa đá",
    }

    def inspect(lock: bool) -> tuple[dict, dict, dict]:
        ps = Product.objects.order_by("pk")
        if lock:
            ps = ps.select_for_update()
        products = {p.code: p for p in ps}
        if set(products) != approved_codes:
            raise CommandError("STOP: Product set drift; will not write")
        for code, target_name, *_ in MENU:
            p = products[code]
            if p.name not in {target_name, legacy_old_names.get(code, target_name)}:
                raise CommandError(f"STOP: Product name drift: {code}")

        old_qs = ProductVariant.objects.exclude(size="FIXED").select_related("product").order_by("pk")
        if lock:
            old_qs = old_qs.select_for_update()
        old = {v.sku: v for v in old_qs}
        old_map = {sku: (v.product.code, v.size, v.volume_ml) for sku, v in old.items()}
        if old_map != legacy_specs or len(old) != 13:
            raise CommandError("STOP: 13 legacy SKU identities drift; will not write")
        old_prices = ChannelPrice.objects.filter(variant__in=list(old.values()))
        if old_prices.count() != 39:
            raise CommandError("STOP: Expected 39 old price records; will not write")

        fixed_qs = ProductVariant.objects.filter(size="FIXED").select_related("product").order_by("pk")
        if lock:
            fixed_qs = fixed_qs.select_for_update()
        fixed = {v.sku: v for v in fixed_qs}
        expected_skus = {f"{code}-{ml}" for code, _, ml, _, _, _ in MENU}
        if not set(fixed).issubset(expected_skus):
            raise CommandError("STOP: Unexpected FIXED SKU")
        for code, name, ml, cost, web, app in MENU:
            sku = f"{code}-{ml}"
            v = fixed.get(sku)
            if v is None:
                if ProductVariant.objects.filter(product=products[code], size="FIXED").exists():
                    raise CommandError(f"STOP: FIXED size collision for {code}")
                continue
            if v.product_id != products[code].pk or v.volume_ml != ml:
                raise CommandError(f"STOP: FIXED SKU mismatch: {sku}")
            prices = list(ChannelPrice.objects.filter(variant=v))
            desired = {"WEB": web, "COUNTER": web, "APP": app}
            if len(prices) > 3 or len({p.channel for p in prices}) != len(prices):
                raise CommandError(f"STOP: Unexpected fixed price rows: {sku}")
            for price in prices:
                if (price.channel not in desired or price.original_price != desired[price.channel]
                        or price.sale_price is not None or price.sale_starts_at is not None
                        or price.sale_ends_at is not None):
                    raise CommandError(f"STOP: Price drift for {sku}/{price.channel}")
            costs = list(StandardCost.objects.filter(variant=v))
            if len(costs) > 1 or (costs and costs[0].ingredient_cost != cost):
                raise CommandError(f"STOP: Cost drift for {sku}")
        if ProductVariant.objects.filter(size="FIXED").count() != len(fixed):
            raise CommandError("STOP: Duplicate or unexpected fixed SKU")
        return products, old, fixed

    with transaction.atomic():
        if args.preview:
            with connection.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
            products, old, fixed = inspect(lock=False)
            print("=== READ ONLY MENU PREVIEW ===")
        else:
            with connection.cursor() as cur:
                cur.execute("SELECT pg_advisory_xact_lock(20261105, 8318)")
            products, old, fixed = inspect(lock=True)

        if args.cutover:
            if len(fixed) != 8:
                raise CommandError("STOP: Stage all eight SKUs before cutover")
            for code, name, ml, cost, web, app in MENU:
                v = fixed[f"{code}-{ml}"]
                if v.is_available:
                    raise CommandError("STOP: New SKU already activated; manual review required")
                if set(ChannelPrice.objects.filter(variant=v).values_list("channel", flat=True)) != {"WEB", "COUNTER", "APP"}:
                    raise CommandError(f"STOP: Price rows incomplete for {v.sku}")
                if not StandardCost.objects.filter(variant=v, ingredient_cost=cost).exists():
                    raise CommandError(f"STOP: Cost missing for {v.sku}")
            for code, name, *_ in MENU:
                p = products[code]
                if p.name != name:
                    p.name = name
                    p.save(update_fields=["name"])
            changed = ProductVariant.objects.filter(pk__in=[v.pk for v in old.values()], is_available=True).update(is_available=False)
            print(f"CUTOVER: 8 approved product names; retired {changed} legacy SKUs; new SKUs remain PAUSED")
        elif args.stage:
            for code, name, ml, cost, web, app in MENU:
                sku = f"{code}-{ml}"
                v = fixed.get(sku)
                if v is None:
                    v = ProductVariant.objects.create(product=products[code], sku=sku,
                                                      size="FIXED", volume_ml=ml, is_available=False)
                if v.is_available:
                    raise CommandError("STOP: Existing fixed SKU already active")
                for channel, price_vnd in (("WEB", web), ("COUNTER", web), ("APP", app)):
                    if not ChannelPrice.objects.filter(variant=v, channel=channel).exists():
                        ChannelPrice.objects.create(variant=v, channel=channel, original_price=price_vnd)
                if not StandardCost.objects.filter(variant=v).exists():
                    StandardCost.objects.create(variant=v, ingredient_cost=cost)
            print("STAGE: Eight PAUSED SKUs, 24 channel prices, eight standard costs prepared")

        print("DATABASE: nau_coffee_dev")
        print("PRODUCTS:", Product.objects.count())
        print("OLD_SKUS:", len(old))
        print("FIXED_SKUS:", ProductVariant.objects.filter(size="FIXED").count())
        print("PRICE_ROWS:", ChannelPrice.objects.count())
        print("STANDARD_COST_ROWS:", StandardCost.objects.count())
        print("OLD_SKUS_AVAILABLE:", ProductVariant.objects.exclude(size="FIXED").filter(is_available=True).count())
        print("FIXED_SKUS_AVAILABLE:", ProductVariant.objects.filter(size="FIXED", is_available=True).count())
        print("ORDER_COUNT_UNTOUCHED:", __import__("commerce.models", fromlist=["Order"]).Order.objects.count())
        if args.preview:
            for code, name, ml, cost, web, app in MENU:
                print(f"PLAN {code}: {name} / {ml}ml / WEB={web} COUNTER={web} APP={app} COST={cost}")
            print("PASS: READ ONLY. NO DATABASE WRITES")
        else:
            print("PASS: ATOMIC MENU OPERATION. NO OLD PRICE/ORDER/CART/BOM CHANGES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        sys.exit(1)
