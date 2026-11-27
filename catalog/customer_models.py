"""Opt-in customer identities; no backfill or changes to Django's User model."""
import uuid
from django.conf import settings
from django.db import models
from django.db.models.functions import Lower, Trim


class CustomerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='customer_profile')
    full_name = models.CharField('Họ và tên', max_length=150)
    phone = models.CharField('Số điện thoại chính', max_length=16, unique=True)
    email = models.EmailField('Email', max_length=254)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    origin = models.CharField(max_length=10, choices=[('PUBLIC', 'Tự đăng ký'), ('STAFF', 'Nhân viên tạo'), ('LEGACY', 'Bổ sung hồ sơ')])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='created_customer_profiles')
    activation_nonce = models.UUIDField(default=uuid.uuid4, editable=False)
    last_email_attempt = models.DateTimeField(null=True, blank=True)
    pending_email = models.EmailField(max_length=254, blank=True)
    pending_phone = models.CharField(max_length=16, blank=True)
    pending_full_name = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hồ sơ khách hàng'
        verbose_name_plural = 'Hồ sơ khách hàng'
        constraints = [
            models.UniqueConstraint(Lower('email'), name='customer_email_ci_unique'),
            models.CheckConstraint(condition=models.Q(email=Lower(Trim('email'))) & ~models.Q(email=''), name='customer_email_canonical'),
            models.CheckConstraint(condition=models.Q(phone__regex=r'^\+84([35789][0-9]{8}|2[0-9]{9})$'), name='customer_phone_canonical'),
        ]


class CounterConsent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)


class CounterCustomerLink(models.Model):
    order = models.OneToOneField('commerce.Order', on_delete=models.PROTECT, related_name='customer_identification')
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='counter_identifications')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='performed_customer_identifications')
    created_at = models.DateTimeField(auto_now_add=True)
    verification = models.CharField(max_length=40, default='VERIFIED_EMAIL_ACCOUNT_CONSENT', editable=False)
