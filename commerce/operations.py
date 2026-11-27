"""Operational rules. Lock order first, then ingredient rows in stable ID order."""
from collections import defaultdict
from datetime import time, timedelta
from decimal import Decimal
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from catalog.permissions import has_role
from catalog.models import ChannelPrice, ProductVariant
from .models import (Ingredient, RecipeLine, OptionRecipeLine, StockMovement, LoyaltyLedger,
    StoreSettings, Order, OrderItem, Payment, PaymentEvent, OrderStatusHistory)


def store(lock=False):
    config, _ = StoreSettings.objects.get_or_create(name='DEMO')
    return StoreSettings.objects.select_for_update().get(pk=config.pk) if lock else config


WEB_SCHEDULE_ERROR = 'Thời gian nhận hàng không hợp lệ, vui lòng chọn lại thời gian nhận hàng.'
WEB_PICKUP_START = time(7, 30)
WEB_ORDER_CUTOFF = time(21, 30)


def validate_web_order_cutoff(selected_for=None):
    """Reject only new same-day WEB orders after 21:30; future preorders remain valid."""
    now = timezone.localtime()
    target_date = timezone.localtime(selected_for).date() if selected_for else now.date()
    current = (now.hour, now.minute, now.second, now.microsecond)
    cutoff = (WEB_ORDER_CUTOFF.hour, WEB_ORDER_CUTOFF.minute, 0, 0)
    if target_date == now.date() and current > cutoff:
        raise ValidationError('Đơn nhận trong ngày được tiếp nhận đến 21:30.')


def _slot_bounds(value):
    """Return the internal 15-minute capacity bucket for an exact promise."""
    start = value.replace(minute=(value.minute // 15) * 15, second=0, microsecond=0)
    return start, start + timedelta(minutes=15)


def _occupied_in_bucket(value, exclude_order_id=None):
    start, end = _slot_bounds(value)
    queryset = Order.objects.filter(scheduled_for__gte=start, scheduled_for__lt=end).exclude(status='CANCELLED')
    if exclude_order_id:
        queryset = queryset.exclude(pk=exclude_order_id)
    return queryset.count()


def scheduled_slot(value=None, earliest=None, *, exact_minute=False, exclude_order_id=None):
    """Caller holds store row lock through order insertion for capacity protection."""
    config = store(lock=True)
    now = timezone.localtime()
    earliest = max(now + timedelta(minutes=config.lead_minutes), earliest or now)
    if value is None:
        candidate = earliest.replace(second=0, microsecond=0)
        candidate += timedelta(minutes=(-candidate.minute % 15))
        if candidate < earliest:
            candidate += timedelta(minutes=15)
        for _ in range((config.preorder_days + 2) * 96):
            if (candidate.date() <= now.date() + timedelta(days=config.preorder_days)
                    and config.opens_at <= candidate.time() < config.closes_at
                    and _occupied_in_bucket(candidate, exclude_order_id) < config.slot_capacity):
                return candidate
            candidate += timedelta(minutes=15)
        raise ValidationError('Chưa có lịch nhận trống. Vui lòng liên hệ Nâu.')
    if timezone.is_naive(value):
        value = timezone.make_aware(value)
    value = timezone.localtime(value)
    pickup_start = max(config.opens_at, WEB_PICKUP_START) if exact_minute else config.opens_at
    within_hours = (pickup_start <= value.time() <= config.closes_at if exact_minute
                    else pickup_start <= value.time() < config.closes_at)
    if (value < earliest or value.date() > now.date() + timedelta(days=config.preorder_days)
            or not within_hours
            or (not exact_minute and value.minute % 15) or value.second or value.microsecond):
        raise ValidationError(WEB_SCHEDULE_ERROR if exact_minute else
            'Chọn lịch 15 phút trong 07:00–22:00 (hoặc giờ cấu hình), sau thời gian chuẩn bị và trong giới hạn đặt trước.')
    if _occupied_in_bucket(value, exclude_order_id) >= config.slot_capacity:
        raise ValidationError(WEB_SCHEDULE_ERROR if exact_minute else 'Lịch nhận đã đầy. Vui lòng chọn giờ khác.')
    return value


def finalize_web_schedule(order, paid_at):
    """Set the pickup promise once, under the store lock, at successful payment."""
    config = store(lock=True)
    if order.scheduled_for:
        candidate = timezone.localtime(order.scheduled_for)
    else:
        candidate = timezone.localtime(paid_at) + timedelta(minutes=30)
        earliest = candidate.replace(hour=WEB_PICKUP_START.hour, minute=WEB_PICKUP_START.minute,
            second=0, microsecond=0)
        candidate = max(candidate, earliest)
    if (candidate.date() > timezone.localdate(paid_at) + timedelta(days=config.preorder_days)
            or candidate < timezone.localtime(paid_at)):
        raise ValidationError(WEB_SCHEDULE_ERROR)
    occupied = _occupied_in_bucket(candidate, order.pk)
    if occupied >= config.slot_capacity:
        raise ValidationError(WEB_SCHEDULE_ERROR)
    if not order.scheduled_for:
        order.scheduled_for = candidate
        order.save(update_fields=['scheduled_for', 'updated_at'])
    return order.scheduled_for


def balance(ingredient):
    return ingredient.movements.aggregate(total=Sum('delta'))['total'] or Decimal(0)


def snapshot_recipe(variant, options):
    """Capture per-drink quantities; Decimal strings keep JSON exact."""
    lines = list(RecipeLine.objects.filter(variant=variant).select_related('ingredient').order_by('ingredient_id'))
    if not lines:
        raise ValidationError(f'Chưa có công thức cho {variant.product.name}; Admin cần cấu hình BOM.')
    for option in options:
        option_id = option.get('id') if isinstance(option, dict) else option.pk
        kind = option.get('kind') if isinstance(option, dict) else option.kind
        option_lines = list(OptionRecipeLine.objects.filter(option_id=option_id).select_related('ingredient').order_by('ingredient_id'))
        if kind == 'TOPPING' and not option_lines:
            raise ValidationError('Topping chưa có BOM; Admin cần cấu hình trước khi nhận đơn.')
        lines.extend(option_lines)
    quantities = defaultdict(Decimal)
    metadata = {}
    for line in lines:
        quantities[line.ingredient_id] += line.quantity
        metadata[line.ingredient_id] = {'ingredient_id': line.ingredient_id,
            'name': line.ingredient.name, 'unit': line.ingredient.unit}
    return [dict(metadata[pk], quantity=str(quantities[pk])) for pk in sorted(quantities)]


def add_requirements(requirements, units, snapshot, quantity):
    if not isinstance(snapshot, list) or not snapshot:
        raise ValidationError('Đơn thiếu bản ghi công thức; cần Admin rà soát trước pha chế.')
    try:
        for line in snapshot:
            pk, unit, amount = line['ingredient_id'], line['unit'], Decimal(line['quantity'])
            if (not isinstance(pk, int) or isinstance(pk, bool) or pk <= 0
                    or not amount.is_finite() or amount <= 0 or unit not in ['g', 'ml', 'piece']
                    or (pk in units and units[pk] != unit)):
                raise ValueError
            requirements[pk] += amount * quantity
            units[pk] = unit
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise ValidationError('Bản ghi công thức không hợp lệ; cần Admin rà soát.') from None


def lock_available_inventory(requirements, units):
    # All callers hold a transaction. Lock ingredient IDs in one stable order.
    ingredients = list(Ingredient.objects.select_for_update().filter(pk__in=requirements).order_by('pk'))
    if len(ingredients) != len(requirements):
        raise ValidationError('Nguyên liệu trong công thức không còn tồn tại; cần Admin rà soát.')
    for ingredient in ingredients:
        if ingredient.unit != units[ingredient.pk]:
            raise ValidationError(f'Đơn vị nguyên liệu {ingredient.name} đã thay đổi; cần Admin rà soát đơn.')
        if not ingredient.is_active or balance(ingredient) < requirements[ingredient.pk]:
            raise ValidationError(f'Không đủ nguyên liệu {ingredient.name}; vui lòng chọn món khác hoặc liên hệ Nâu.')
    return ingredients


@transaction.atomic
def check_order_inventory(lines):
    """Validate aggregated order supply without deducting or reserving stock.

    Recheck at PREPARING: adjustments or other orders can consume stock later.
    """
    snapshots, requirements, units = [], defaultdict(Decimal), {}
    for variant, quantity, options in lines:
        snapshot = snapshot_recipe(variant, options)
        add_requirements(requirements, units, snapshot, quantity)
        snapshots.append(snapshot)
    if not snapshots:
        raise ValidationError('Đơn chưa có món để kiểm tra nguyên liệu.')
    lock_available_inventory(requirements, units)
    return snapshots


def consume_stock(order, actor):
    if StockMovement.objects.filter(order=order, reason='CONSUME').exists():
        return
    requirements = defaultdict(Decimal)
    units, legacy = {}, []
    items = list(order.items.select_related('variant__product').order_by('pk'))
    if not items:
        raise ValidationError('Đơn chưa có món để pha chế.')
    for item in items:
        snapshot = item.recipe_snapshot
        if snapshot is None:
            if not RecipeLine.objects.filter(variant=item.variant).exists():
                raise ValidationError('Đơn cũ thiếu công thức đã lưu và SKU cũ không còn BOM. '
                    'Admin cần xác minh công thức trước khi pha; hệ thống không tự dùng công thức SKU mới.')
            snapshot = snapshot_recipe(item.variant, item.options_snapshot)
            legacy.append((item, snapshot))
        add_requirements(requirements, units, snapshot, item.quantity)
    ingredients = lock_available_inventory(requirements, units)
    # Legacy recipes are captured only on the first successful preparation, not
    # backfilled as though they were known at the time of the original checkout.
    for item, snapshot in legacy:
        item.recipe_snapshot = snapshot
        item.save(update_fields=['recipe_snapshot'])
    if legacy:
        OrderStatusHistory.objects.create(order=order, from_state=order.status, to_state=order.status,
            actor=actor, reason='Đơn cũ: chốt công thức hiện tại ở lần bắt đầu pha chế, không phải công thức lịch sử lúc đặt.')
    for ingredient in ingredients:
        quantity = requirements[ingredient.pk]
        StockMovement.objects.create(ingredient=ingredient, delta=-quantity, reason='CONSUME',
            note='Tiêu hao theo công thức đã lưu của đơn DEMO khi bắt đầu pha chế', order=order, actor=actor,
            idempotency_key=f'consume:{order.pk}:{ingredient.pk}')


@transaction.atomic
def adjust_stock(actor, ingredient_id, delta, note, key, reason='ADJUST'):
    if not (has_role(actor, 'ADMIN') or (has_role(actor, 'STAFF') and actor.has_perm('commerce.add_stockmovement'))):
        raise PermissionDenied
    if not delta or not note.strip() or reason not in ['PURCHASE', 'ADJUST', 'WASTE']:
        raise ValidationError('Cần lượng biến động khác 0 và lý do hợp lệ.')
    if (reason == 'PURCHASE' and delta < 0) or (reason == 'WASTE' and delta > 0):
        raise ValidationError('Nhập kho phải tăng, hao hụt phải giảm.')
    ingredient = Ingredient.objects.select_for_update().get(pk=ingredient_id)
    existing = StockMovement.objects.filter(idempotency_key=str(key)).first()
    if existing:
        if existing.ingredient_id != ingredient.pk or existing.delta != delta or existing.actor_id != actor.pk:
            raise ValidationError('Mã giao dịch đã dùng cho biến động khác.')
        return existing
    if balance(ingredient) + delta < 0:
        raise ValidationError('Không thể làm tồn kho âm.')
    return StockMovement.objects.create(ingredient=ingredient, delta=delta, note=note.strip(), actor=actor,
        reason=reason, idempotency_key=str(key))


def award_loyalty(order):
    if order.user_id and order.status == 'COMPLETED' and order.payment.status == 'PAID':
        config = store()
        LoyaltyLedger.objects.get_or_create(order=order, event='EARN', defaults={
            'user_id': order.user_id, 'delta': (order.subtotal - order.discount) // config.loyalty_vnd_per_point})


@transaction.atomic
def verify_delivery(actor, code, distance, reason):
    if not has_role(actor, 'STAFF', 'ADMIN'):
        raise PermissionDenied
    order = Order.objects.select_for_update().get(public_code=code)
    if order.fulfillment != 'DELIVERY' or order.status not in ['PENDING_PAYMENT', 'CONFIRMED']:
        raise ValidationError('Chỉ xác minh đơn giao trước pha chế.')
    if not distance.is_finite() or not Decimal(0) <= distance <= Decimal(3) or not reason.strip():
        raise ValidationError('Cần lý do xác minh và khoảng cách trong 0–3 km; không giả định tọa độ.')
    order.delivery_distance_km, order.delivery_verified = distance, True
    order.save(update_fields=['delivery_distance_km', 'delivery_verified', 'updated_at'])
    OrderStatusHistory.objects.create(order=order, from_state=order.status, to_state=order.status,
        actor=actor, reason=f'Nhân viên xác minh thủ công {distance} km: {reason}'[:300])
    return order


@transaction.atomic
def manual_order(actor, data, lines):
    if not has_role(actor, 'STAFF', 'ADMIN'):
        raise PermissionDenied
    from django.contrib.auth import get_user_model
    from .services import validate_configuration
    get_user_model().objects.select_for_update().get(pk=actor.pk)
    existing = Order.objects.filter(placed_by=actor, channel__in=['APP', 'COUNTER'], idempotency_key=data['idempotency_key']).first()
    if data.get('channel')=='APP' and data.get('voucher'):
        raise ValidationError('Đơn APP không được dùng voucher.')
    if existing:
        return existing
    if data['channel'] not in ['APP', 'COUNTER']:
        raise ValidationError('Chỉ nhập đơn APP/COUNTER.')
    from catalog.customer_accounts import confirm_counter_customer
    customer_profile = confirm_counter_customer(actor, data, consume=False)
    reference = data.get('external_reference', '').strip()
    if data['channel'] == 'APP' and not reference:
        raise ValidationError('Đơn APP cần mã tham chiếu bên ngoài để chống trùng.')
    slot = scheduled_slot(data.get('scheduled_for'))
    if reference and Order.objects.filter(channel=data['channel'], external_reference=reference).exists():
        raise ValidationError('Mã tham chiếu đã có đơn. Không tạo bản sao.')
    quoted=quote_manual(actor,data,lines)
    rows,subtotal=quoted['rows'],quoted['subtotal']
    if not rows:
        raise ValidationError('Cần ít nhất một món.')
    snapshots = check_order_inventory([(variant, qty, options) for variant, qty, options, unit in rows])
    order = Order.objects.create(user=customer_profile.user if customer_profile else None, placed_by=actor, channel=data['channel'], fulfillment='PICKUP',
        customer_name=customer_profile.full_name if customer_profile else data['customer_name'],
        phone=customer_profile.phone if customer_profile else data.get('phone', ''), notes=data.get('notes', ''),
        external_reference=reference, scheduled_for=slot, subtotal=subtotal, discount=quoted['discount'], total=quoted['total'],
        status='CONFIRMED', idempotency_key=data['idempotency_key'])
    for (variant, qty, options, unit), snapshot in zip(rows, snapshots):
        OrderItem.objects.create(order=order, variant=variant, product_name=variant.product.name, sku=variant.sku,
            quantity=qty, unit_price=unit, line_total=unit * qty, recipe_snapshot=snapshot, options_snapshot=[{
                'id': opt.pk, 'name': opt.name, 'kind': opt.kind, 'price_delta': opt.price_delta} for opt in options])
    Payment.objects.create(order=order, method='EXTERNAL_DEMO' if data['channel'] == 'APP' else 'PAY_AT_PICKUP',
        status='UNPAID', amount=order.total)
    OrderStatusHistory.objects.create(order=order, to_state='CONFIRMED', actor=actor, reason=f'Nhập tay {data["channel"]} DEMO; chưa đối soát tiền')
    if quoted['voucher']:
        from .vouchers import record_use
        record_use(order,customer_profile.user,quoted['voucher'],quoted['voucher_policy'])
    if customer_profile:
        confirm_counter_customer(actor,data)
        from catalog.customer_models import CounterCustomerLink
        CounterCustomerLink.objects.create(order=order, customer=customer_profile.user, actor=actor)
    return order


@transaction.atomic
def reconcile_external(actor, code):
    if not has_role(actor, 'STAFF', 'ADMIN'):
        raise PermissionDenied
    order = Order.objects.select_for_update().get(public_code=code)
    payment = Payment.objects.select_for_update().get(order=order)
    if order.channel != 'APP' or payment.method != 'EXTERNAL_DEMO' or order.status in ['CANCELLED', 'DELIVERY_FAILED']:
        raise ValidationError('Chỉ đối soát mô phỏng đơn APP hợp lệ.')
    if payment.status != 'PAID':
        payment.status, payment.paid_at = 'PAID', timezone.now()
        payment.save(update_fields=['status', 'paid_at', 'updated_at'])
        PaymentEvent.objects.get_or_create(payment=payment, event_key='external_demo', defaults={'actor': actor})
    return order


@transaction.atomic
def quote_manual(actor,data,lines):
    if not has_role(actor,'STAFF','ADMIN'):raise PermissionDenied
    from .services import validate_configuration
    from catalog.customer_accounts import confirm_counter_customer
    if data['channel'] not in ('COUNTER','APP'):raise ValidationError('Kênh không hợp lệ.')
    if data['channel']=='APP' and data.get('voucher'):raise ValidationError('Đơn APP không được dùng voucher.')
    customer_profile=confirm_counter_customer(actor,data,consume=False)
    rows, subtotal = [], 0
    for line in lines:
        variant = ProductVariant.objects.select_related('product__category').get(pk=line['variant'].pk)
        if not 1 <= line['quantity'] <= 99:
            raise ValidationError('Số lượng phải từ 1–99.')
        options, _ = validate_configuration(variant, [opt.pk for opt in line.get('options', [])])
        price = ChannelPrice.objects.select_for_update().filter(variant=variant, channel=data['channel']).first()
        if not price:
            raise ValidationError('SKU chưa có giá cho kênh đã chọn.')
        unit = price.current_price + sum(opt.price_delta for opt in options)
        rows.append((variant, line['quantity'], options, unit))
        subtotal += unit * line['quantity']
    from .vouchers import quote_selection
    has_sale=any(p.current_price<p.original_price for p in ChannelPrice.objects.filter(variant__in=[r[0] for r in rows],channel=data['channel']))
    voucher,discount,policy=quote_selection(data.get('voucher'),customer_profile.user if customer_profile else None,data['channel'],subtotal,has_sale)
    return {'rows':rows,'subtotal':subtotal,'discount':discount,'total':subtotal-discount,'voucher':voucher,
            'voucher_policy':policy,'customer':customer_profile.user if customer_profile else None}
