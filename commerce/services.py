"""Cart ownership and configuration validation; prices always read server-side."""
import hashlib
import uuid
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from catalog.models import ProductOption, ProductVariant
from .models import Cart, CartItem


@transaction.atomic
def quote_cart(cart, user=None, fulfillment='PICKUP', voucher_code='', voucher_id=None):
    from catalog.models import ChannelPrice
    from django.utils import timezone
    from .models import Voucher
    if fulfillment != 'PICKUP':
        raise ValidationError('Website chỉ nhận đặt trước và nhận tại quán.')
    if fulfillment not in ['PICKUP', 'DELIVERY']:
        raise ValidationError('Phương thức nhận không hợp lệ.')
    rows, subtotal, has_sale = [], 0, False
    for item in cart.items.select_related('variant__product__category').order_by('pk'):
        options, _ = validate_configuration(item.variant, item.options.values_list('pk', flat=True))
        price = ChannelPrice.objects.select_for_update().filter(variant=item.variant, channel='WEB').first()
        if not price:
            raise ValidationError('Món chưa có giá bán website.')
        current = price.current_price
        unit = current + sum(option.price_delta for option in options)
        has_sale |= current < price.original_price
        total = unit * item.quantity
        rows.append({'item': item, 'unit': unit, 'total': total, 'options': options})
        subtotal += total
    if not rows:
        raise ValidationError('Giỏ hàng trống.')
    voucher, discount, policy = None, 0, None
    from . import vouchers as voucher_engine
    if voucher_id not in (None,''):
        if voucher_code.strip():raise ValidationError('Một đơn chỉ được chọn một voucher.')
        voucher,discount,policy=voucher_engine.quote_selection(voucher_id,user,'WEB',subtotal,has_sale)
    if voucher_code.strip():
        voucher = Voucher.objects.select_for_update().filter(code__iexact=voucher_code.strip(), is_active=True).first()
        now = timezone.now()
        if voucher and voucher_engine.campaign_for(voucher):
            raise ValidationError('Campaign mới phải được chọn từ danh sách.')
        if not voucher or not voucher.starts_at <= now < voucher.ends_at:
            raise ValidationError('Voucher không tồn tại hoặc đã hết hạn.')
        if not user or not user.is_authenticated:
            raise ValidationError('Đăng nhập để sử dụng voucher.')
        redemptions = voucher.redemptions.filter(is_active=True)
        if (subtotal < voucher.min_subtotal or redemptions.count() >= voucher.max_uses
                or redemptions.filter(user=user).count() >= voucher.per_user_limit):
            raise ValidationError('Voucher không đáp ứng giá trị tối thiểu hoặc đã hết lượt.')
        if has_sale and not voucher.allow_sale_stacking:
            raise ValidationError('Voucher không cộng dồn với giá khuyến mại.')
        discount = subtotal * voucher.amount // 100 if voucher.kind == 'PERCENT' else voucher.amount
        if voucher.cap is not None:
            discount = min(discount, voucher.cap)
        discount = min(discount, subtotal)
    shipping = 0
    return {'rows': rows, 'subtotal': subtotal, 'discount': discount, 'shipping': shipping,
        'total': subtotal - discount + shipping, 'voucher': voucher, 'voucher_policy':policy}


@transaction.atomic
def place_order(user, cart, data):
    from catalog.permissions import has_role
    from .models import Order, OrderItem, Payment, OrderStatusHistory
    if not has_role(user, 'CUSTOMER', 'STAFF', 'ADMIN'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    # Validate policy even on idempotent retries before returning an existing order.
    if data.get('fulfillment') != 'PICKUP':
        raise ValidationError('Website chỉ nhận đặt trước và nhận tại quán.')
    if data.get('payment_method') != 'MOCK_ONLINE':
        raise ValidationError('Website chỉ hỗ trợ thanh toán online mô phỏng.')
    get_user_model().objects.select_for_update().get(pk=user.pk)
    existing = Order.objects.filter(user=user, idempotency_key=data['idempotency_key']).first()
    if existing:
        return existing
    cart = Cart.objects.select_for_update().get(pk=cart.pk, user=user)
    fulfillment, method = data['fulfillment'], data['payment_method']
    from .operations import scheduled_slot, check_order_inventory, validate_web_order_cutoff
    selected_schedule = data.get('scheduled_for')
    validate_web_order_cutoff(selected_schedule)
    menu_started = data.get('menu_started_at') or timezone.now()
    scheduled_for = scheduled_slot(selected_schedule, menu_started + timedelta(minutes=35), exact_minute=True) if selected_schedule else None
    quote = quote_cart(cart, user, fulfillment, data.get('voucher_code', ''),data.get('voucher'))
    snapshots = check_order_inventory([(row['item'].variant, row['item'].quantity, row['options']) for row in quote['rows']])
    order = Order.objects.create(user=user, placed_by=user if has_role(user, 'STAFF', 'ADMIN') else None,
        fulfillment=fulfillment, customer_name=data['customer_name'], phone=data['phone'],
        address=data.get('address', '') if fulfillment == 'DELIVERY' else '', notes=data.get('notes', ''),
        subtotal=quote['subtotal'], discount=quote['discount'], shipping=quote['shipping'], total=quote['total'],
        status='PENDING_PAYMENT',
        idempotency_key=data['idempotency_key'], scheduled_for=scheduled_for)
    for row, snapshot in zip(quote['rows'], snapshots):
        item = row['item']
        OrderItem.objects.create(order=order, variant=item.variant, product_name=item.variant.product.name,
            sku=item.variant.sku, unit_price=row['unit'], quantity=item.quantity, line_total=row['total'], recipe_snapshot=snapshot,
            options_snapshot=[{'id': option.pk, 'name': option.name, 'kind': option.kind, 'price_delta': option.price_delta} for option in row['options']])
    Payment.objects.create(order=order, method=method, amount=order.total,
        status='PENDING')
    OrderStatusHistory.objects.create(order=order, from_state='', to_state=order.status, actor=user, reason='Tạo đơn WEB DEMO')
    if quote['voucher']:
        from .vouchers import record_use
        record_use(order,user,quote['voucher'],quote['voucher_policy'])
    cart.items.all().delete()
    return order


def _history(order, target, actor, reason):
    from .models import OrderStatusHistory
    OrderStatusHistory.objects.create(order=order, from_state=order.status, to_state=target, actor=actor, reason=reason)
    order.status = target
    order.save(update_fields=['status', 'updated_at'])


@transaction.atomic
def simulate_payment(user, token, success, scheduled_for=None):
    from .models import Payment, PaymentEvent, Order
    from django.shortcuts import get_object_or_404
    from django.utils import timezone
    payment = get_object_or_404(Payment, token=token, order__user=user, method='MOCK_ONLINE')
    order = Order.objects.select_for_update().get(pk=payment.order_id)
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if order.status != 'PENDING_PAYMENT' or payment.status == 'PAID':
        return order
    if success and scheduled_for is not None:
        from .operations import scheduled_slot
        order.scheduled_for = scheduled_slot(scheduled_for, timezone.now(), exact_minute=True,
            exclude_order_id=order.pk)
        order.save(update_fields=['scheduled_for', 'updated_at'])
    key = 'mock_success' if success else 'mock_failure'
    PaymentEvent.objects.get_or_create(payment=payment, event_key=key, defaults={'actor': user})
    paid_at = timezone.now() if success else None
    if success:
        from .operations import finalize_web_schedule
        finalize_web_schedule(order, paid_at)
    payment.status = 'PAID' if success else 'FAILED'
    payment.paid_at = paid_at
    payment.save(update_fields=['status', 'paid_at', 'updated_at'])
    if success:
        _history(order, 'CONFIRMED', user, 'Thanh toán thành công MÔ PHỎNG')
    return order


@transaction.atomic
def transition_order(actor, code, target, reason=''):
    from .models import Order, Payment, PaymentEvent
    from catalog.permissions import has_role
    from django.core.exceptions import PermissionDenied
    from django.shortcuts import get_object_or_404
    staff = has_role(actor, 'STAFF', 'ADMIN')
    queryset = Order.objects.all() if staff else Order.objects.filter(user=actor)
    order = get_object_or_404(queryset.select_for_update(), public_code=code)
    if not staff and target != 'CANCELLED':
        raise PermissionDenied
    if order.status == target:
        return order
    graph = {'PENDING_CONFIRMATION': ['CONFIRMED', 'CANCELLED'],
             'PENDING_PAYMENT': ['CANCELLED'], 'CONFIRMED': ['PREPARING', 'CANCELLED'],
        'PREPARING': ['READY'], 'READY': ['PICKUP_WAITING'] if order.fulfillment == 'PICKUP' else ['DELIVERING'],
        'PICKUP_WAITING': ['COMPLETED'], 'DELIVERING': ['COMPLETED', 'DELIVERY_FAILED']}
    if target not in graph.get(order.status, []):
        raise ValidationError('Không thể chuyển trạng thái này. Hãy làm theo thứ tự xử lý.' if staff else 'Khách chỉ hủy trước pha chế.')
    if order.status == 'PENDING_CONFIRMATION' and target == 'CONFIRMED':
        if not staff or order.fulfillment != 'DELIVERY' or not settings.NAU_DEMO_DELIVERY_ENABLED:
            raise ValidationError('Không thể xác nhận đơn giao mô phỏng trong trạng thái hiện tại.')
        from .demo_delivery import quote_demo_delivery, DemoDeliveryError, delivery_deadline
        from django.utils import timezone
        try:
            fresh = quote_demo_delivery(order.address, order.subtotal, order.discount)
        except DemoDeliveryError as exc:
            raise ValidationError(str(exc)) from exc
        if (order.delivery_distance_km != Decimal(fresh.distance_meters) / Decimal(1000)
                or order.shipping != fresh.shipping_vnd):
            raise ValidationError('Địa chỉ/khoảng cách/phí giao đã thay đổi. Không tự xác nhận đơn.')
        order.delivery_verified = True
        order.bill_issued_at = timezone.now()
        order.delivery_deadline_at = delivery_deadline(order.bill_issued_at)
        order.save(update_fields=['delivery_verified', 'bill_issued_at', 'delivery_deadline_at', 'updated_at'])
    if target == 'PREPARING' and order.fulfillment == 'DELIVERY' and not order.delivery_verified:
        raise ValidationError('Chưa xác minh địa chỉ giao trong phạm vi 3 km; liên hệ khách trước xử lý.')
    if target == 'PREPARING' and order.payment.method == 'BANK_TRANSFER_DEMO' and order.payment.status != 'PAID':
        raise ValidationError('Chưa xác nhận chuyển khoản mô phỏng; không thể pha chế.')
    if target == 'DELIVERY_FAILED' and not reason.strip():
        raise ValidationError('Cần lý do giao thất bại.')
    from .operations import consume_stock, award_loyalty
    if target == 'PREPARING':
        payment = Payment.objects.select_for_update().get(order=order)
        if payment.method == 'MOCK_ONLINE' and payment.status != 'PAID':
            raise ValidationError('Chưa thanh toán thành công; không thể pha chế.')
        consume_stock(order, actor)
    if target == 'COMPLETED' and order.fulfillment == 'DELIVERY' and order.bill_issued_at:
        from django.utils import timezone
        order.delivered_at = timezone.now()
        order.save(update_fields=['delivered_at', 'updated_at'])
    _history(order, target, actor, reason[:300])
    if target == 'COMPLETED':
        award_loyalty(order)
    if target == 'CANCELLED':
        from .vouchers import has_new_policy
        if hasattr(order, 'redemption') and not has_new_policy(order.redemption):
            order.redemption.is_active = False
            order.redemption.save(update_fields=['is_active'])
        payment = Payment.objects.select_for_update().get(order=order)
        if payment.status == 'PAID' and payment.method in ('MOCK_ONLINE', 'BANK_TRANSFER_DEMO'):
            payment.status = 'REFUND_PENDING'
            payment.save(update_fields=['status', 'updated_at'])
            PaymentEvent.objects.get_or_create(payment=payment, event_key='refund_requested', defaults={'actor': actor})
    return order


@transaction.atomic
def capture_cash(actor, code):
    from catalog.permissions import has_role
    from .models import Order, Payment, PaymentEvent
    from django.core.exceptions import PermissionDenied
    from django.utils import timezone
    if not has_role(actor, 'STAFF', 'ADMIN'):
        raise PermissionDenied
    order = Order.objects.select_for_update().get(public_code=code)
    payment = Payment.objects.select_for_update().get(order=order)
    if payment.method not in ['COD', 'PAY_AT_PICKUP'] or order.status in ['CANCELLED', 'PENDING_PAYMENT', 'PENDING_CONFIRMATION', 'DELIVERY_FAILED']:
        raise ValidationError('Không thể ghi nhận tiền cho đơn này.')
    if (settings.NAU_DEMO_DELIVERY_ENABLED and order.fulfillment == 'DELIVERY'
            and payment.method == 'COD' and order.status != 'COMPLETED'):
        raise ValidationError('Chỉ ghi nhận COD khi đã giao hàng thành công.')
    if payment.status != 'PAID':
        payment.status, payment.paid_at = 'PAID', timezone.now()
        payment.save(update_fields=['status', 'paid_at', 'updated_at'])
        PaymentEvent.objects.get_or_create(payment=payment, event_key='cash_demo', defaults={'actor': actor})
    from .operations import award_loyalty
    award_loyalty(order)
    return order


@transaction.atomic
def verify_demo_transfer(actor, code):
    """Staff-only manual confirmation; NEVER contacts a bank or charges money."""
    from django.core.exceptions import PermissionDenied
    from django.utils import timezone
    from .models import Order, Payment, PaymentEvent
    from catalog.permissions import has_role
    if not has_role(actor, 'STAFF', 'ADMIN'):
        raise PermissionDenied
    order = Order.objects.select_for_update().get(public_code=code)
    payment = Payment.objects.select_for_update().get(order=order)
    if (order.fulfillment != 'DELIVERY' or order.status != 'CONFIRMED'
            or payment.method != 'BANK_TRANSFER_DEMO' or not settings.NAU_DEMO_DELIVERY_ENABLED):
        raise ValidationError('Không thể xác nhận chuyển khoản của đơn này.')
    if payment.status == 'PAID':
        return order
    if payment.status != 'UNPAID':
        raise ValidationError('Trạng thái thanh toán không hợp lệ.')
    payment.status, payment.paid_at = 'PAID', timezone.now()
    payment.save(update_fields=['status', 'paid_at', 'updated_at'])
    PaymentEvent.objects.get_or_create(payment=payment, event_key='bank_transfer_demo',
        defaults={'actor': actor})
    return order


@transaction.atomic
def refund_mock(actor, code, *, strict=False):
    from catalog.permissions import has_role
    from django.core.exceptions import PermissionDenied
    from django.utils import timezone
    from .models import Order, Payment, PaymentEvent
    if not has_role(actor, 'ADMIN'):
        raise PermissionDenied
    order = Order.objects.select_for_update().get(public_code=code)
    payment = Payment.objects.select_for_update().get(order=order)
    if payment.status == 'REFUNDED':
        if strict:
            raise ValidationError('Đơn đã hoàn tiền mô phỏng; không tạo giao dịch hoàn lần hai.')
        return order
    if order.status != 'CANCELLED' or payment.method not in ('MOCK_ONLINE', 'BANK_TRANSFER_DEMO') or payment.status != 'REFUND_PENDING':
        raise ValidationError('Chỉ hoàn mô phỏng cho đơn hủy đã thanh toán mock.')
    payment.status, payment.refunded_at = 'REFUNDED', timezone.now()
    payment.save(update_fields=['status', 'refunded_at', 'updated_at'])
    PaymentEvent.objects.get_or_create(payment=payment, event_key='mock_refund', defaults={'actor': actor})
    return order


@transaction.atomic
def get_cart(request):
    guest_key = request.session.get('guest_cart_key')
    if request.user.is_authenticated:
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        Cart.objects.select_for_update().get(pk=cart.pk)
        guest = Cart.objects.select_for_update().filter(session_key=guest_key).first() if guest_key else None
        if guest:
            for item in guest.items.prefetch_related('options'):
                existing = cart.items.filter(variant=item.variant, config_key=item.config_key).first()
                if existing:
                    existing.quantity = min(99, existing.quantity + item.quantity)
                    existing.save(update_fields=['quantity', 'updated_at'])
                else:
                    item.cart = cart
                    item.save(update_fields=['cart', 'updated_at'])
            # Only the temporary guest cart belonging to this session is consumed.
            guest.delete()
            request.session.pop('guest_cart_key', None)
        return cart
    if not guest_key:
        guest_key = str(uuid.uuid4())
        request.session['guest_cart_key'] = guest_key
    cart, _ = Cart.objects.get_or_create(session_key=guest_key)
    return cart


def validate_configuration(variant, option_ids):
    from catalog.approved_menu import enabled, check_channel_price
    if enabled():
        if variant.size != 'FIXED':
            raise ValidationError('Lựa chọn cũ đã ngừng bán; vui lòng chọn lại dung tích chuẩn.')
        if list(option_ids):
            raise ValidationError('Menu chuẩn chưa hỗ trợ tùy chọn hoặc phụ thu.')
        check_channel_price(variant)
    if not variant.is_available or not variant.product.is_active or not variant.product.category.is_active:
        raise ValidationError('Món tạm chưa nhận đặt; vui lòng quay lại sau.')
    try:
        ids = sorted(set(int(value) for value in option_ids))
    except (TypeError, ValueError):
        raise ValidationError('Tùy chọn không hợp lệ.') from None
    options = list(ProductOption.objects.filter(pk__in=ids, product=variant.product, is_active=True).order_by('pk'))
    if len(options) != len(ids):
        raise ValidationError('Tùy chọn không thuộc món hoặc đã ngừng bán.')
    for kind in ['SUGAR', 'ICE']:
        if sum(option.kind == kind for option in options) > 1:
            raise ValidationError('Chỉ chọn một mức đường và một mức đá.')
    return options, hashlib.sha256(','.join(map(str, ids)).encode()).hexdigest()


@transaction.atomic
def add_item(cart, variant_id, quantity, option_ids=()):
    if not isinstance(quantity, int) or isinstance(quantity, bool) or not 1 <= quantity <= 99:
        raise ValidationError('Số lượng phải từ 1 đến 99.')
    Cart.objects.select_for_update().get(pk=cart.pk)
    variant = ProductVariant.objects.select_related('product__category').get(pk=variant_id)
    options, key = validate_configuration(variant, option_ids)
    item, created = CartItem.objects.get_or_create(cart=cart, variant=variant, config_key=key,
        defaults={'quantity': quantity})
    if not created:
        if item.quantity + quantity > 99:
            raise ValidationError('Tối đa 99 ly cho cùng cấu hình.')
        item.quantity += quantity
        item.save(update_fields=['quantity', 'updated_at'])
    item.options.set(options)
    return item
