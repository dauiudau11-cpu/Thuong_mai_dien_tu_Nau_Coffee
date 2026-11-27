from .approved_menu import enabled

def standard_menu(request):
    from django.conf import settings
    from django.db.models import Sum
    from catalog.store_identity import STORE
    from commerce.models import CartItem
    if request.user.is_authenticated:
        cart_quantity = CartItem.objects.filter(cart__user=request.user).aggregate(total=Sum('quantity'))['total'] or 0
    else:
        guest_key = request.session.get('guest_cart_key')
        cart_quantity = (CartItem.objects.filter(cart__session_key=guest_key).aggregate(total=Sum('quantity'))['total'] or 0
                         if guest_key else 0)
    return {'store_info':STORE, 'policy_consent_enabled':settings.NAU_POLICY_CONSENT_ENABLED,
        'standard_menu_enabled': enabled(), 'customer_accounts_enabled': settings.NAU_CUSTOMER_ACCOUNTS_ENABLED,
        'vouchers_v2_enabled': settings.NAU_VOUCHERS_V2_ENABLED, 'cart_quantity': cart_quantity}
