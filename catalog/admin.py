from django.contrib import admin
from .models import Category, Product, ProductVariant, ChannelPrice, ProductImage, ProductOption, StandardCost
from django import forms
from django.db import transaction
from .permissions import has_role
from .approved_menu import enabled


from .admin_localization import VietnameseAdminMixin


class ImageInline(VietnameseAdminMixin, admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'is_active', 'is_featured']
    list_filter = ['category', 'is_active']
    search_fields = ['code', 'name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ImageInline]


class PriceForm(forms.ModelForm):
    class Meta:
        model = ChannelPrice
        fields = '__all__'

    def clean(self):
        values = super().clean()
        variant = values.get('variant')
        if variant and variant.size == 'FIXED':
            if values.get('sale_price') is not None:
                raise forms.ValidationError('Menu chuẩn chưa có khuyến mại được phê duyệt.')
            if self.instance.pk and (variant.pk != self.instance.variant_id or values.get('channel') != self.instance.channel):
                raise forms.ValidationError('Không chuyển SKU hoặc kênh của bản ghi giá chuẩn.')
        return values


@admin.register(ChannelPrice)
class PriceAdmin(admin.ModelAdmin):
    form = PriceForm

    @transaction.atomic
    def save_model(self, request, obj, form, change):
        ProductVariant.objects.select_for_update().get(pk=obj.variant_id)
        super().save_model(request, obj, form, change)
        if obj.variant.size == 'FIXED' and obj.channel in ('WEB', 'COUNTER'):
            ChannelPrice.objects.update_or_create(variant=obj.variant,
                channel='COUNTER' if obj.channel == 'WEB' else 'WEB',
                defaults={'original_price': obj.original_price, 'sale_price': None,
                          'sale_starts_at': None, 'sale_ends_at': None})

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj) and (obj is None or obj.variant.size != 'FIXED')

    actions = None

    list_display = ['variant', 'channel', 'original_price', 'sale_price', 'sale_ends_at']
    list_filter = ['channel']
    search_fields = ['variant__sku', 'variant__product__name']


admin.site.register(Category)
admin.site.register(ProductVariant)
admin.site.register(ProductImage)
admin.site.register(ProductOption)


@admin.register(StandardCost)
class StandardCostAdmin(admin.ModelAdmin):
    list_display = ['variant', 'ingredient_cost']

    def has_module_permission(self, request):
        return enabled() and has_role(request.user, 'ADMIN') and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return enabled() and has_role(request.user, 'ADMIN') and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return enabled() and has_role(request.user, 'ADMIN') and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return enabled() and has_role(request.user, 'ADMIN') and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False
