"""Operator mailbox exists only in the explicitly selected localhost settings."""
from django.urls import path
from .urls import urlpatterns as business_patterns
from .local_preview import mailbox
urlpatterns = [path('__local/mail/', mailbox, name='local_mailbox'),
    path('__local/mail/<uuid:message_id>/', mailbox, name='local_mail')] + business_patterns
