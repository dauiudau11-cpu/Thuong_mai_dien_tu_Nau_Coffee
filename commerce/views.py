from django.conf import settings
import uuid
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from catalog.models import ProductVariant
from catalog.permissions import customer_required, public_customer_only, roles_required, has_role
from .forms import AddItemForm, CheckoutForm
from .models import Cart, CartItem, Order, Payment, Voucher
from .services import get_cart, add_item, quote_cart, place_order, simulate_payment, transition_order, capture_cash, refund_mock


@public_customer_only
def cart(request):
    own_cart = get_cart(request)
    quote = None
    try:
        if own_cart.items.exists():
            quote = quote_cart(own_cart)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    items = list(own_cart.items.select_related('variant__product').prefetch_related('options').order_by('pk'))
    return render(request, 'commerce/cart.html', {
        'cart': own_cart, 'cart_items': items, 'quote': quote,
        'basket_quantity': sum(item.quantity for item in items),
    })


@require_POST
@public_customer_only
def cart_add(request):
    form = AddItemForm(request.POST)
    if form.is_valid():
        get_object_or_404(ProductVariant, pk=form.cleaned_data['variant'])
        try:
            add_item(get_cart(request), form.cleaned_data['variant'], form.cleaned_data['quantity'], request.POST.getlist('options'))
            messages.success(request, 'Đã thêm món vào giỏ.')
            if request.POST.get('action') == 'buy_now':
                return redirect('checkout')
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
    else:
        messages.error(request, 'Số lượng hoặc món không hợp lệ.')
    return redirect('cart')


@require_POST
@public_customer_only
def cart_update(request, pk):
    from django.db import transaction
    from django.http import JsonResponse
    live = request.headers.get('Accept') == 'application/json'
    with transaction.atomic():
        own = get_cart(request)
        Cart.objects.select_for_update().get(pk=own.pk)
        item = get_object_or_404(CartItem, pk=pk, cart=own)
        quantity = request.POST.get('quantity', '')
        if not (quantity.isascii() and quantity.isdigit() and 1 <= int(quantity) <= 99):
            if live:
                return JsonResponse({'error': 'Số lượng phải từ 1 đến 99.'}, status=400)
            messages.error(request, 'Số lượng phải từ 1 đến 99.')
            return redirect('cart')
        item.quantity = int(quantity)
        item.save(update_fields=['quantity', 'updated_at'])
        if live:
            try:
                quote = quote_cart(own)
            except ValidationError as error:
                transaction.set_rollback(True)
                return JsonResponse({'error': ' '.join(error.messages)}, status=422)
            return JsonResponse({
                'quantity': sum(row['item'].quantity for row in quote['rows']),
                'subtotal': quote['subtotal'], 'discount': quote['discount'], 'total': quote['total'],
                'rows': [{'id': row['item'].pk, 'quantity': row['item'].quantity,
                          'unit': row['unit'], 'total': row['total']} for row in quote['rows']],
            })
    return redirect('cart')


@require_POST
@public_customer_only
def cart_remove(request, pk):
    from django.db import transaction
    with transaction.atomic():
        own = get_cart(request)
        Cart.objects.select_for_update().get(pk=own.pk)
        get_object_or_404(CartItem, pk=pk, cart=own).delete()
    return redirect('cart')


@customer_required
def checkout(request):
    own_cart = get_cart(request)
    if request.method == 'GET' and not own_cart.items.exists():
        return render(request, 'commerce/checkout.html', {'empty_cart': True})
    token = request.session.setdefault('checkout_key', str(uuid.uuid4()))
    if request.method == 'GET' and own_cart.items.exists() and Order.objects.filter(user=request.user, idempotency_key=token).exists():
        token = str(uuid.uuid4())
        request.session['checkout_key'] = token
    profile = getattr(request.user, 'customer_profile', None)
    receiver_name = getattr(profile, 'full_name', '') or request.user.get_full_name()
    receiver_phone = getattr(profile, 'phone', '')
    form = CheckoutForm(request.POST if request.method == 'POST' else None, initial={
        'idempotency_key': token, 'fulfillment': 'PICKUP', 'payment_method': 'MOCK_ONLINE',
        'customer_name': receiver_name, 'phone': receiver_phone}, user=request.user, request=request)
    quote = None
    if request.method == 'POST' and form.is_valid():
        try:
            if str(form.cleaned_data['idempotency_key']) != token:
                raise ValidationError('Phiên xác nhận không hợp lệ. Hãy tải lại bước thanh toán.')
            if request.POST.get('action') == 'place':
                from support import policies
                order = policies.place_order(request, own_cart, form.cleaned_data) if policies.enabled() else place_order(request.user, own_cart, form.cleaned_data)
                if order.status == Order.Status.PENDING_PAYMENT and order.payment.method == Payment.Method.MOCK_ONLINE:
                    return redirect('mock_payment', token=order.payment.token)
                return redirect('order_detail', code=order.public_code)
            quote = quote_cart(own_cart, request.user, form.cleaned_data['fulfillment'], form.cleaned_data.get('voucher_code',''), form.cleaned_data.get('voucher'))
        except ValidationError as error:
            form.add_error(None, error)
    elif request.method == 'GET':
        try:
            quote = quote_cart(own_cart, request.user)
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
    return render(request, 'commerce/checkout.html', {
        'form': form, 'quote': quote, 'receiver_name': receiver_name,
        'receiver_phone': receiver_phone, 'contact_ready': bool(receiver_name and receiver_phone),
    })


@customer_required
def orders(request):
    queryset = Order.objects.filter(user=request.user).select_related('payment').prefetch_related('items')
    tab = request.GET.get('tab', 'all')
    if tab not in ('all', 'processing', 'paid', 'history'):
        tab = 'all'
    closed = [Order.Status.COMPLETED, Order.Status.CANCELLED, Order.Status.DELIVERY_FAILED]
    if tab == 'processing':
        queryset = queryset.exclude(status__in=closed)
    elif tab == 'paid':
        queryset = queryset.filter(payment__status=Payment.Status.PAID)
    elif tab == 'history':
        queryset = queryset.filter(status__in=closed)
    query = request.GET.get('q', '').strip()[:80]
    if query:
        queryset = queryset.filter(public_code__icontains=query)
    if request.GET.get('status') in Order.Status.values:
        queryset = queryset.filter(status=request.GET['status'])
    return render(request, 'commerce/orders.html', {'page_obj': Paginator(queryset, 20).get_page(request.GET.get('page')), 'states': Order.Status.choices, 'active_tab': tab})


@customer_required
def order_detail(request, code):
    order = get_object_or_404(Order, public_code=code, user=request.user)
    from .refunds import refund_context
    return render(request, 'commerce/order.html', {'order': order, **refund_context(order)})


@customer_required
@require_POST
def cancel(request, code):
    get_object_or_404(Order, public_code=code, user=request.user)
    try:
        transition_order(request.user, code, 'CANCELLED', 'Khách yêu cầu hủy')
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    return redirect('order_detail', code=code)


@customer_required
def mock_payment(request, token):
    from .forms import PaymentScheduleForm
    payment = get_object_or_404(Payment, token=token, order__user=request.user, method='MOCK_ONLINE')
    if request.method == 'POST':
        schedule_form = PaymentScheduleForm(request.POST)
        if request.POST.get('outcome') not in ['success', 'failure']:
            messages.error(request, 'Kết quả mô phỏng không hợp lệ.')
        elif not schedule_form.is_valid():
            return render(request, 'commerce/payment.html', {'payment': payment, 'schedule_form': schedule_form})
        else:
            try:
                simulate_payment(request.user, token, request.POST['outcome'] == 'success',
                    scheduled_for=schedule_form.cleaned_data['scheduled_for'])
            except ValidationError as error:
                schedule_form.add_error(None, error)
                payment.refresh_from_db()
                return render(request, 'commerce/payment.html', {'payment': payment, 'schedule_form': schedule_form})
        return redirect('order_detail', code=payment.order.public_code)
    initial = {}
    if payment.order.scheduled_for:
        selected = timezone.localtime(payment.order.scheduled_for)
        initial = {'scheduled_date': selected.date(), 'scheduled_hour': f'{selected.hour:02d}',
            'scheduled_minute': f'{selected.minute:02d}'}
    return render(request, 'commerce/payment.html', {'payment': payment,
        'schedule_form': PaymentScheduleForm(initial=initial)})


@roles_required('STAFF', 'ADMIN')
def queue(request):
    queryset = Order.objects.all()
    if not request.GET.get('status'):
        queryset = queryset.filter(status__in=['CONFIRMED', 'PREPARING', 'READY', 'PICKUP_WAITING', 'DELIVERING'])
    query = request.GET.get('q', '').strip()[:150]
    if query:
        queryset = queryset.filter(Q(public_code__icontains=query) | Q(customer_name__icontains=query))
    if request.GET.get('channel') in ['WEB', 'COUNTER', 'APP']:
        queryset = queryset.filter(channel=request.GET['channel'])
    if request.GET.get('fulfillment') in ['PICKUP', 'DELIVERY']:
        queryset = queryset.filter(fulfillment=request.GET['fulfillment'])
    if request.GET.get('status') in Order.Status.values:
        queryset = queryset.filter(status=request.GET['status'])
    return render(request, 'commerce/queue.html', {'page_obj': Paginator(queryset.select_related('payment'), 20).get_page(request.GET.get('page')),
        'states': Order.Status.choices, 'can_refund': has_role(request.user, 'ADMIN'),
        'demo_delivery_enabled': settings.NAU_DEMO_DELIVERY_ENABLED})


@roles_required('STAFF', 'ADMIN')
@require_POST
def transition(request, code):
    current = get_object_or_404(Order, public_code=code)
    try:
        if current.fulfillment == 'PICKUP' and current.channel in ('WEB', 'COUNTER') and not has_role(request.user, 'ADMIN'):
            raise ValidationError('Dùng ba nút trên Kanban để kiểm tra phiên bản đơn trước khi xử lý.')
        if current.status == request.POST.get('status'):
            raise ValidationError('Đơn đã ở trạng thái này; không có chuyển trạng thái mới.')
        transition_order(request.user, code, request.POST.get('status'), request.POST.get('reason', ''))
    except ValidationError as error:
        import logging
        logging.getLogger('nau.staff').warning('Transition rejected: order=%s target=%s', code, request.POST.get('status', '')[:30])
        messages.error(request, ' '.join(error.messages))
    return redirect('queue')


@roles_required('STAFF', 'ADMIN')
@require_POST
def cash(request, code):
    get_object_or_404(Order, public_code=code)
    try:
        capture_cash(request.user, code)
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    return redirect('queue')


def promotions(request):
    from django.utils import timezone
    now = timezone.now()
    vouchers=Voucher.objects.filter(is_active=True).order_by('ends_at','code')
    cards=[]
    for voucher in vouchers:
        campaign=getattr(voucher,'campaign_v2',None)
        if campaign and campaign.audience == 'PRIVATE' and not request.user.is_authenticated:
            continue
        used=False
        if request.user.is_authenticated:
            if campaign and campaign.audience == 'PUBLIC':
                used=campaign.uses.filter(user=request.user).exists()
            elif campaign and campaign.audience == 'PRIVATE':
                grant=campaign.grants.filter(user=request.user).first()
                if not grant: continue
                used=grant.used >= grant.allocated
            elif not campaign:
                used=voucher.redemptions.filter(user=request.user,is_active=True).count() >= voucher.per_user_limit
        expired=now >= voucher.ends_at
        cards.append({'voucher':voucher,'used':used,'expired':expired,'usable':not used and not expired and voucher.starts_at <= now})
    state=request.GET.get('state','all')
    if state == 'usable': cards=[card for card in cards if card['usable']]
    elif state == 'used': cards=[card for card in cards if card['used']]
    return render(request,'commerce/promotions.html',{'voucher_cards':cards,'voucher_state':state})


@roles_required('ADMIN')
@require_POST
def refund(request, code):
    order = get_object_or_404(Order.objects.select_related('payment'), public_code=code)
    try:
        if order.payment.status == 'REFUNDED':
            raise ValidationError('Đơn đã hoàn tiền mô phỏng; không tạo giao dịch hoàn lần hai.')
        refund_mock(request.user, code, strict=True)
        messages.success(request, 'Đã xác nhận hoàn tiền mô phỏng. Không phát sinh tiền thật.')
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    return redirect('refunds' if request.POST.get('return_to') == 'refunds' else 'queue')


@roles_required('ADMIN')
def refunds(request):
    if request.method != 'GET':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET'])
    status = request.GET.get('payment_status', 'REFUND_PENDING')
    if status not in ('REFUND_PENDING','REFUNDED'):
        status = 'REFUND_PENDING'
    orders = Order.objects.filter(status='CANCELLED',payment__status=status,
        payment__method__in=['MOCK_ONLINE','BANK_TRANSFER_DEMO']).select_related('payment').order_by('updated_at','pk')
    from .refunds import refund_context
    page = Paginator(orders,20).get_page(request.GET.get('page'))
    return render(request,'commerce/refunds.html',{'page_obj':page,'refund_rows':[(o,refund_context(o)) for o in page], 'payment_status':status})


def delivery_partners(request):
    return render(request, 'commerce/delivery_partners.html', {'partners': (
        ('GrabFood', 'grabfood-official.png', 'Khám phá đồ ăn và thức uống trên GrabFood.', 'https://food.grab.com/vn/vi/'),
        ('ShopeeFood', 'shopeefood-official.svg', 'Tìm lựa chọn giao tận nơi trên ShopeeFood.', 'https://shopeefood.vn/'),
        ('beFood', 'be-logo-yellow.png', 'Khám phá lựa chọn giao món trên beFood.', 'https://food.be.com.vn/'),
    )})
