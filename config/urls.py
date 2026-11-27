from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from catalog import views
from catalog import account_views
from catalog import reference_views
from support import views as support_views
from support import policy_views

urlpatterns = [
    path('policies/', policy_views.center, name='policy_center'),
    path('account/privacy/', policy_views.preferences, name='policy_preferences'),
    path('', include('catalog.customer_urls')),
    path('dashboard/kitchen/', reference_views.kitchen, name='kitchen'),
    path('dashboard/manage/<slug:section>/', reference_views.management, name='reference_management'),
    path('dashboard/settings/<slug:section>/', reference_views.configuration, name='reference_configuration'),
    path('contact/', support_views.contact, name='contact'),
    path('feedback/', support_views.contact, {'kind': 'FEEDBACK'}, name='feedback'),
    path('policies/<slug:slug>/', support_views.policy, name='policy'),
    path('products/<slug:slug>/reviews/', support_views.review, name='review'),
    path('', include('commerce.urls')),
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('ve-nau/', views.about, name='about'),
    path('menu/', views.menu, name='menu'),
    path('products/<slug:slug>/', views.product_detail, name='product'),
    path('accounts/register/', views.register, name='register'),
    path('accounts/login/', account_views.LimitedLoginView.as_view(), name='login'),
    path('internal/login/', account_views.InternalLoginView.as_view(), name='internal_login'),
    path('account/profile/', account_views.profile, name='profile'),
    path('account/addresses/', account_views.addresses, name='addresses'),
    path('account/addresses/<int:pk>/edit/', account_views.addresses, name='address_edit'),
    path('account/addresses/<int:pk>/remove/', account_views.remove_address, name='address_remove'),
    path('account/password/', auth_views.PasswordChangeView.as_view(template_name='registration/password_change.html', success_url='/account/'), name='password_change'),
    path('accounts/logout/', account_views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('healthz/', views.health, name='health'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
