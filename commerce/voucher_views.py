"""Feature-gated quotes and campaign administration; quotes never redeem."""
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters
from catalog.permissions import roles_required
from . import vouchers
from .models import Cart, VoucherCampaign
# Preserve the public import path for existing callers.
from .voucher_forms import CampaignForm, GrantForm  # noqa: F401
from .services import quote_cart
from .operation_forms import ManualLines
from .operations import quote_manual

def require_enabled():
    if not vouchers.enabled():
        raise Http404

def selection(request):
    if request.POST.get('voucher_code') or len(request.POST.getlist('voucher')) > 1:
        raise ValidationError('Chỉ chọn một voucher từ danh sách.')
    return request.POST.get('voucher', '')

def response_for(quote, user, channel):
    return JsonResponse({key: quote[key] for key in ('subtotal', 'discount', 'total')} | {'choices': vouchers.available(user, channel)})

@roles_required('CUSTOMER', 'STAFF', 'ADMIN')
@require_POST
def web_quote(request):
    require_enabled()
    try:
        cart = Cart.objects.filter(user=request.user).first()
        if not cart:
            raise ValidationError('Giỏ hàng trống.')
        quote = quote_cart(cart, request.user, voucher_id=selection(request))
        return response_for(quote, request.user, 'WEB')
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=400)

@roles_required('STAFF', 'ADMIN')
@require_POST
@sensitive_post_parameters('customer_consent')
def counter_quote(request):
    require_enabled()
    try:
        selected = selection(request)
        lines = ManualLines(request.POST, prefix='lines')
        if not lines.is_valid():
            raise ValidationError('Kiểm tra các dòng món và số lượng.')
        data = {key: request.POST.get(key, '') for key in ('channel', 'phone', 'customer_selection', 'customer_consent')}
        data['confirm_customer'] = request.POST.get('confirm_customer') == 'on'
        data['customer_selection_context'] = request.session.get('counter_selection_context', '')
        data['voucher'] = selected
        quote = quote_manual(request.user, data, [line.cleaned_data for line in lines if line.cleaned_data and (not line.cleaned_data.get('DELETE'))])
        return response_for(quote, quote['customer'], data['channel'])
    except ValidationError as error:
        return JsonResponse({'error': ' '.join(error.messages)}, status=400)

@roles_required('ADMIN')
def campaigns(request):
    from .voucher_management import index
    return index(request)


@roles_required('ADMIN')
def campaign_detail(request, pk):
    from .voucher_management import detail
    campaign = get_object_or_404(VoucherCampaign, pk=pk)
    return detail(request, campaign.voucher_id)
