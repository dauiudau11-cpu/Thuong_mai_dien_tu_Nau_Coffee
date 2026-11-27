import csv
import uuid
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Sum, Count, Q, F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters
from catalog.permissions import roles_required, has_role
from .models import Ingredient, StockMovement, LoyaltyLedger, Order, OrderItem
from .operations import adjust_stock, verify_delivery, manual_order, reconcile_external
from .operation_forms import ManualOrderForm, ManualLines, StockForm, DeliveryForm, ReportForm


@roles_required('STAFF', 'ADMIN')
@sensitive_post_parameters('customer_consent')
def new_manual(request):
    token = request.session.setdefault('manual_order_key', str(uuid.uuid4()))
    if request.method == 'GET' and Order.objects.filter(placed_by=request.user, idempotency_key=token).exists():
        token = str(uuid.uuid4())
        request.session['manual_order_key'] = token
    form = ManualOrderForm(request.POST if request.method == 'POST' else None, initial={'idempotency_key': token, 'customer_selection': request.session.get('counter_customer_selection', ''),
        'phone': request.session.get('counter_customer_phone', ''),
        'customer_name': request.session.get('counter_customer_name', '')})
    lines = ManualLines(request.POST if request.method == 'POST' else None, prefix='lines')
    valid = form.is_valid() if request.method == 'POST' else False
    lines_valid = lines.is_valid() if request.method == 'POST' else False
    if request.method == 'POST' and valid and lines_valid:
        try:
            if str(form.cleaned_data['idempotency_key']) != token:
                raise ValidationError('Phiên nhập đơn không hợp lệ.')
            order_data = dict(form.cleaned_data)
            # Trusted session context only: never accept the value from POST.
            order_data['customer_selection_context'] = request.session.get('counter_selection_context', '')
            order = manual_order(request.user, order_data, [line.cleaned_data for line in lines if line.cleaned_data and not line.cleaned_data.get('DELETE')])
            for key in ('counter_customer_selection', 'counter_customer_phone', 'counter_customer_name', 'counter_selection_context'):
                request.session.pop(key, None)
            messages.success(request, f'Đã tạo đơn {order.public_code}, chưa ghi nhận thanh toán mô phỏng.')
            return redirect('queue')
        except ValidationError as error:
            form.add_error(None, error)
        except IntegrityError:
            form.add_error(None, 'Mã tham chiếu hoặc yêu cầu đã tồn tại. Kiểm tra danh sách đơn trước khi thử lại.')
    # Presentation-only metadata; manual_order still computes/validates all prices.
    from catalog.models import ProductVariant, ProductOption
    from catalog.approved_menu import enabled
    catalog = {'variants': [], 'options': list(ProductOption.objects.filter(is_active=True).values('id', 'product_id', 'price_delta'))}
    for variant in ProductVariant.objects.filter(is_available=True, product__is_active=True,
            product__category__is_active=True).prefetch_related('prices'):
        if enabled() and variant.size != 'FIXED':
            continue
        catalog['variants'].append({'id': variant.pk, 'product_id': variant.product_id,
            'name': variant.product.name, 'sku': variant.sku, 'image': variant.product.image_url,
            'prices': {price.channel: price.current_price for price in variant.prices.all() if price.channel in ['COUNTER', 'APP']}})
    if enabled():
        catalog['options'] = []
    return render(request, 'commerce/manual.html', {'form': form, 'lines': lines, 'manual_catalog': catalog})


@roles_required('STAFF', 'ADMIN')
def inventory(request):
    can_adjust = has_role(request.user, 'ADMIN') or request.user.has_perm('commerce.add_stockmovement')
    form = StockForm(request.POST if request.method == 'POST' else None, initial={'key': uuid.uuid4()})
    if request.method == 'POST':
        if form.is_valid():
            try:
                adjust_stock(request.user, form.cleaned_data['ingredient'].pk, form.cleaned_data['delta'],
                    form.cleaned_data['note'], form.cleaned_data['key'], form.cleaned_data['reason'])
                messages.success(request, 'Đã ghi biến động kho.')
                return redirect('inventory')
            except ValidationError as error:
                form.add_error(None, error)
    ingredients = Ingredient.objects.annotate(stock=Sum('movements__delta')).order_by('sku')
    return render(request, 'commerce/inventory.html', {'ingredients': ingredients, 'form': form,
        'can_adjust': can_adjust, 'movements': Paginator(StockMovement.objects.select_related('ingredient', 'actor'), 25).get_page(request.GET.get('page'))})


@roles_required('STAFF', 'ADMIN')
@require_POST
def delivery(request, code):
    get_object_or_404(Order, public_code=code)
    form = DeliveryForm(request.POST)
    if form.is_valid():
        try:
            verify_delivery(request.user, code, form.cleaned_data['distance'], form.cleaned_data['reason'])
            messages.success(request, 'Đã lưu xác minh thủ công; không phải định vị tự động.')
        except ValidationError as error:
            messages.error(request, ' '.join(error.messages))
    else:
        messages.error(request, 'Cần khoảng cách 0–3 km và căn cứ xác minh.')
    return redirect('queue')


@roles_required('STAFF', 'ADMIN')
@require_POST
def transfer(request, code):
    get_object_or_404(Order, public_code=code)
    from .services import verify_demo_transfer
    try:
        verify_demo_transfer(request.user, code)
        messages.success(request, 'Đã xác nhận chuyển khoản MÔ PHỎNG; không có giao dịch ngân hàng.')
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    return redirect('queue')


@roles_required('STAFF', 'ADMIN')
@require_POST
def external(request, code):
    get_object_or_404(Order, public_code=code)
    try:
        reconcile_external(request.user, code)
        messages.success(request, 'Đã ghi đối soát bên ngoài MÔ PHỎNG.')
    except ValidationError as error:
        messages.error(request, ' '.join(error.messages))
    return redirect('queue')


@login_required
def loyalty(request):
    entries = LoyaltyLedger.objects.filter(user=request.user).select_related('order')
    return render(request, 'commerce/loyalty.html', {'balance': entries.aggregate(total=Sum('delta'))['total'] or 0,
        'page_obj': Paginator(entries, 20).get_page(request.GET.get('page'))})


@roles_required('ADMIN')
def reports(request):
    form = ReportForm(request.GET)
    queryset = Order.objects.all()
    if form.is_valid():
        values = form.cleaned_data
        if values.get('start'):
            queryset = queryset.filter(created_at__date__gte=values['start'])
        if values.get('end'):
            queryset = queryset.filter(created_at__date__lte=values['end'])
        if values.get('channel'):
            queryset = queryset.filter(channel=values['channel'])
    else:
        queryset = queryset.none()
    active = queryset.exclude(status='CANCELLED')
    # Values are demo order value, never real revenue. Collected includes only PAID.
    summary = active.aggregate(net=Sum(F('subtotal') - F('discount')), orders=Count('pk'),
        gross=Sum('subtotal'), discount=Sum('discount'), shipping=Sum('shipping'),
        collected=Sum('payment__amount', filter=Q(payment__status='PAID')))
    channels = active.values('channel').annotate(net=Sum(F('subtotal') - F('discount')),
        orders=Count('pk'), gross=Sum('subtotal'), discount=Sum('discount'), shipping=Sum('shipping'),
        collected=Sum('payment__amount', filter=Q(payment__status='PAID'))).order_by('channel')
    total = queryset.count()
    cancelled = queryset.filter(status='CANCELLED').count()
    if request.GET.get('format') == 'csv' and form.is_valid():
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="nau-demo-report.csv"'
        writer = csv.writer(response)
        writer.writerow(['channel', 'orders', 'gross_demo', 'discount', 'shipping', 'net_order_value_demo', 'collected_demo'])
        for row in channels:
            writer.writerow([row[key] or 0 for key in ['channel', 'orders', 'gross', 'discount', 'shipping', 'net', 'collected']])
        return response
    products = OrderItem.objects.filter(order__in=active).values('sku', 'product_name').annotate(
        quantity=Sum('quantity'), value=Sum('line_total')).order_by('-quantity', 'sku')[:10]
    query = request.GET.copy()
    query['format'] = 'csv'
    return render(request, 'commerce/reports.html', {'form': form, 'summary': summary, 'channels': channels,
        'products': products, 'cancelled': cancelled, 'total': total,
        'cancel_rate': round(cancelled * 100 / total, 1) if total else 0,
        'aov': (summary['net'] or 0) // summary['orders'] if summary['orders'] else 0,
        'csv_query': query.urlencode()})
