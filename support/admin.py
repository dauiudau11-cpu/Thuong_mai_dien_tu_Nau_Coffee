from django.contrib import admin
from .models import Message, Review, Policy

from .policy_admin import PolicyAdmin,ConsentAdmin
from .models import ConsentEvent
admin.site.register(Policy,PolicyAdmin)
admin.site.register(ConsentEvent,ConsentAdmin)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'kind', 'status', 'created_at']
    list_filter = ['kind', 'status']
    search_fields = ['subject', 'name']
    readonly_fields = ['kind', 'user', 'order', 'name', 'email', 'subject', 'body', 'created_at', 'updated_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'rating', 'status', 'created_at']
    list_filter = ['status', 'rating']
    readonly_fields = ['item', 'user', 'product', 'rating', 'body', 'created_at', 'moderated_by']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.moderated_by = request.user
        super().save_model(request, obj, form, change)
