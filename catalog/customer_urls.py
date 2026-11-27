from django.urls import path
from . import customer_views as views
from . import password_reset as recovery

urlpatterns = [
    path('accounts/password/reset/', recovery.request_reset, name='customer_password_reset'),
    path('accounts/password/reset/done/', recovery.reset_done, name='customer_password_reset_done'),
    path('accounts/password/reset/confirm/', recovery.exchange, name='customer_password_reset_exchange'),
    path('accounts/password/reset/new/', recovery.confirm, name='customer_password_reset_confirm'),
    path('accounts/password/reset/complete/', recovery.complete, name='customer_password_reset_complete'),
    path('dashboard/customers/clear/', views.clear_selection, name='customer_clear_selection'),
    path('accounts/activate/', views.activate, name='customer_activate'),
    path('accounts/activation/resend/', views.resend, name='customer_activation_resend'),
    path('account/counter-consent/', views.counter_consent, name='customer_counter_consent'),
    path('dashboard/customers/lookup/', views.lookup, name='customer_lookup'),
    path('dashboard/customers/create/', views.staff_create, name='staff_customer_create'),
    path('dashboard/customers/<int:pk>/resend/', views.staff_resend, name='staff_customer_resend'),
]
