from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'


class NauAdminConfig(AdminConfig):
    default_site = 'catalog.admin_site.NauAdminSite'
