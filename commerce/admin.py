from django.contrib import admin
from .models import (Cart, CartItem, Order, OrderItem, Payment, PaymentEvent,
    OrderStatusHistory, Voucher, VoucherRedemption, StoreSettings)


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(ReadOnlyAdmin):
    list_display = ['public_code', 'channel', 'status', 'fulfillment', 'total', 'created_at']
    search_fields = ['public_code', 'customer_name']
    list_filter = ['channel', 'status', 'fulfillment']


@admin.register(Payment)
class PaymentAdmin(ReadOnlyAdmin):
    list_display = ['order', 'method', 'status', 'amount', 'paid_at']
    list_filter = ['method', 'status']


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ['code', 'kind', 'amount', 'min_subtotal', 'starts_at', 'ends_at', 'is_active']
    list_filter = ['is_active', 'kind']
    search_fields = ['code']

    def changelist_view(self, request, extra_context=None):
        from . import vouchers
        if vouchers.enabled() and request.POST.get('action') not in self.get_actions(request):
            from django.core.exceptions import PermissionDenied
            if not self.has_view_or_change_permission(request):raise PermissionDenied
            if request.method=='POST':
                required=self.has_add_permission(request) if request.POST.get('action')=='campaign' else self.has_change_permission(request)
                if not required:raise PermissionDenied
            from .voucher_management import index
            return index(request)
        return super().changelist_view(request, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        from . import vouchers
        if vouchers.enabled():
            from django.core.exceptions import PermissionDenied
            if not self.has_add_permission(request):raise PermissionDenied
            from .voucher_management import create
            return create(request)
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        from . import vouchers
        if vouchers.enabled():
            from django.core.exceptions import PermissionDenied
            obj=self.get_object(request, object_id)
            if obj is None or not self.has_view_or_change_permission(request,obj):raise PermissionDenied
            if request.method=='POST' and not self.has_change_permission(request,obj):raise PermissionDenied
            from .voucher_management import editor
            return editor(request,obj,read_only=not self.has_change_permission(request,obj))
        return super().change_view(request, object_id, form_url, extra_context)


admin.site.register(StoreSettings)
from .models import Ingredient, RecipeLine, OptionRecipeLine, StockMovement, LoyaltyLedger


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'unit', 'low_stock_threshold', 'is_active']
    search_fields = ['sku', 'name']


admin.site.register(RecipeLine)
admin.site.register(OptionRecipeLine)
admin.site.register(StockMovement, ReadOnlyAdmin)
admin.site.register(LoyaltyLedger, ReadOnlyAdmin)
for model in [Cart, CartItem, OrderItem, PaymentEvent, OrderStatusHistory, VoucherRedemption]:
    admin.site.register(model, ReadOnlyAdmin)
