from django.contrib.admin import AdminSite
from .permissions import has_role


class NauAdminSite(AdminSite):
    site_header = 'Nâu Coffee — Quản trị hệ thống'
    site_title = 'Quản trị Nâu Coffee'
    index_title = 'Quản trị hệ thống'

    def register(self, model_or_iterable, admin_class=None, **options):
        from django.contrib.admin import ModelAdmin
        from .admin_localization import VietnameseAdminMixin
        base = admin_class or ModelAdmin
        localized = type('Vietnamese' + base.__name__, (VietnameseAdminMixin, base), {})
        return super().register(model_or_iterable, localized, **options)

    def get_app_list(self, request, app_label=None):
        from .localization import MODEL_NAMES, model_name
        apps = super().get_app_list(request, app_label)
        for app in apps:
            app['name'] = MODEL_NAMES.get(app['app_label'], (app['name'], {}))[0]
            for entry in app['models']:
                entry['name'] = model_name(entry['model'])
        return apps

    def index(self, request, extra_context=None):
        context = dict(extra_context or {})
        if self.has_permission(request):
            from .traffic import dashboard
            context['traffic'] = dashboard(request.GET.get('period', '7'))
        return super().index(request, extra_context=context)

    def has_permission(self, request):
        return has_role(request.user, 'ADMIN') and request.user.is_staff
