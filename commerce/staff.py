"""Staff V2 projections and locked commands; no schema or catalogue mutations."""
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST
from catalog.permissions import roles_required
from .models import Order, Payment
from .services import transition_order, capture_cash


class StaleOrder(ValidationError):
    pass


def version(order):
    return f'{order.updated_at.isoformat()}:{order.payment.updated_at.isoformat()}'


def action_for(order):
    if order.fulfillment != 'PICKUP' or order.channel not in ('WEB', 'COUNTER'):
        return ''
    if order.payment.method == 'MOCK_ONLINE' and order.payment.status != 'PAID':
        return ''
    return {'CONFIRMED': 'start', 'PREPARING': 'finish', 'PICKUP_WAITING': 'handover',
            'READY': 'wait'}.get(order.status, '')


@transaction.atomic
def staff_command(actor, code, action, expected_version, confirmed=False):
    from catalog.permissions import has_role
    from django.core.exceptions import PermissionDenied
    if not has_role(actor, 'STAFF', 'ADMIN'):
        raise PermissionDenied
    order = get_object_or_404(Order.objects.select_for_update(), public_code=code)
    # Match the lock order used by payment/cancel/prepare services.
    order.payment = Payment.objects.select_for_update().get(order=order)
    if not expected_version or version(order) != expected_version:
        raise StaleOrder('Đơn đã thay đổi trên thiết bị khác. Đã đồng bộ; hãy kiểm tra trước khi thử lại.')
    if order.status == 'COMPLETED':
        raise ValidationError('Đơn đã hoàn tất; chi tiết chỉ đọc.')
    if order.fulfillment != 'PICKUP' or order.channel not in ('WEB', 'COUNTER'):
        raise ValidationError('Đơn này dùng quy trình lịch sử / APP riêng tại danh sách đơn.')
    if action == 'cash':
        if order.payment.method not in ('PAY_AT_PICKUP', 'COD') or order.payment.status != 'UNPAID':
            raise ValidationError('Đơn không cần ghi nhận thu tiền. MOCK_ONLINE do khách thanh toán mô phỏng.')
        capture_cash(actor, code)
    else:
        if action_for(order) != action or not action:
            raise ValidationError('Thao tác không phù hợp trạng thái hoặc thanh toán hiện tại.')
        if action == 'handover' and not confirmed:
            raise ValidationError('Vui lòng xác nhận đã bàn giao đúng đơn cho khách.')
        states = {'start': ['PREPARING'], 'finish': ['READY', 'PICKUP_WAITING'],
                  'wait': ['PICKUP_WAITING'], 'handover': ['COMPLETED']}[action]
        for state in states:
            transition_order(actor, code, state, 'Staff V2: ' + action)
    return Order.objects.select_related('payment').get(pk=order.pk)


def card_context(order):
    blocked = order.status != 'COMPLETED' and any(item.recipe_snapshot is None and not item.variant.recipe.exists() for item in order.items.all())
    return {'order': order, 'action': '' if blocked else action_for(order), 'blocked': blocked, 'version': version(order),
            'can_cash': order.channel == 'COUNTER' and order.fulfillment == 'PICKUP'
                and order.payment.method in ('PAY_AT_PICKUP', 'COD')
                and order.payment.status == 'UNPAID' and order.status not in ('COMPLETED', 'CANCELLED')}


def board_columns():
    base = Order.objects.select_related('payment').prefetch_related('items')
    definitions = [('confirmed', 'Chờ pha chế', ['CONFIRMED']),
                   ('preparing', 'Đang pha', ['PREPARING']),
                   ('waiting', 'Chờ khách nhận', ['PICKUP_WAITING']),
                   ('completed', 'Hoàn tất', ['COMPLETED'])]
    normal = base.filter(fulfillment='PICKUP', channel__in=['WEB', 'COUNTER']).exclude(
        payment__method='MOCK_ONLINE', payment__status__in=['PENDING', 'UNPAID', 'FAILED', 'REFUND_PENDING', 'REFUNDED'])
    columns = []
    blocked_cards = []
    for key, title, statuses in definitions:
        qs = normal.filter(status__in=statuses).order_by('-created_at' if key == 'completed' else 'created_at', 'pk')
        orders = list(qs[:30])
        cards = [card_context(o) for o in orders]
        blocked = [c for c in cards if c['blocked'] and key != 'completed']
        blocked_cards.extend(blocked)
        columns.append({'key': key, 'title': title, 'count': qs.count() - len(blocked), 'orders': orders,
                        'cards': [c for c in cards if c not in blocked]})
    legacy = base.exclude(fulfillment='PICKUP', channel__in=['WEB', 'COUNTER']).exclude(status__in=['CANCELLED', 'COMPLETED']).order_by('created_at', 'pk')
    exceptional = base.filter(fulfillment='PICKUP', channel__in=['WEB', 'COUNTER']).filter(
        status__in=['READY', 'PENDING_CONFIRMATION', 'DELIVERY_FAILED']).order_by('created_at', 'pk')
    # Confirmed mock orders with inconsistent payment are visible as exceptions, never actionable.
    inconsistent = base.filter(fulfillment='PICKUP', channel__in=['WEB','COUNTER'],
        status__in=['CONFIRMED','PREPARING','PICKUP_WAITING'], payment__method='MOCK_ONLINE').exclude(payment__status='PAID')
    exceptions = list((exceptional | inconsistent).distinct()[:30])
    return columns, list(legacy[:30]), blocked_cards + [card_context(o) for o in exceptions]


@roles_required('STAFF', 'ADMIN')
@require_GET
def board(request):
    columns, legacy, exceptions = board_columns()
    return render(request, 'reference/kitchen.html', {'columns': columns, 'legacy_orders': legacy, 'exceptions': exceptions})


@roles_required('STAFF', 'ADMIN')
@require_GET
def board_data(request):
    columns, legacy, exceptions = board_columns()
    html = render_to_string('commerce/staff_columns.html', {'columns': columns, 'legacy_orders': legacy, 'exceptions': exceptions}, request=request)
    return JsonResponse({'html': html})


@roles_required('STAFF', 'ADMIN')
@require_GET
def detail(request, code):
    order = get_object_or_404(Order.objects.select_related('payment').prefetch_related('items', 'history'), public_code=code)
    events = list(order.history.order_by('created_at', 'pk'))
    transitions = [e for e in events if e.from_state != e.to_state]
    activity = [e for e in events if e.from_state == e.to_state]
    times = {state: next((e.created_at for e in transitions if e.to_state == state), None)
             for state in ['PREPARING', 'COMPLETED']}
    html = render_to_string('commerce/staff_detail.html', {'order': order, 'transitions': transitions,
        'activity': activity, 'prepared_at': times['PREPARING'], 'completed_at': times['COMPLETED']}, request=request)
    return JsonResponse({'html': html, 'version': version(order), 'status': order.status})


@roles_required('STAFF', 'ADMIN')
@require_POST
def command(request, code):
    try:
        order = staff_command(request.user, code, request.POST.get('action'), request.POST.get('version'),
                              request.POST.get('confirmed') == 'yes')
    except ValidationError as exc:
        return JsonResponse({'ok': False, 'error': ' '.join(exc.messages)}, status=409 if isinstance(exc, StaleOrder) else 400)
    return JsonResponse({'ok': True, 'status': order.status, 'payment_status': order.payment.status,
                         'version': version(order), 'message': 'Đã cập nhật đơn.'})
