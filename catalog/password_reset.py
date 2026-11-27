"""Customer-only recovery using Django's standard password reset tokens/forms.
Tokens travel in URL fragments and CSRF-protected POST, never supported URL paths.
"""
import hashlib
import smtplib
import time
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.functions import Lower, Trim
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_GET
from support.models import SubmissionLimit
from .customer_accounts import email_ready, normalize_email, enabled
from .customer_models import CustomerProfile
from .customer_views import feature

UID_KEY = '_customer_password_reset_uid'
TOKEN_KEY = '_customer_password_reset_token'


class CustomerSetPasswordForm(SetPasswordForm):
    """Translate display errors only; all validation/save logic remains Django's."""
    display_messages = {
        'password_too_short': 'Mật khẩu phải có ít nhất %(min_length)d ký tự.',
        'password_too_common': 'Mật khẩu này quá phổ biến. Hãy chọn mật khẩu khác.',
        'password_entirely_numeric': 'Mật khẩu không được chỉ gồm chữ số.',
        'password_too_similar': 'Mật khẩu quá giống thông tin tài khoản của bạn.',
        'password_mismatch': 'Hai lần nhập mật khẩu chưa khớp.',
    }

    def add_error(self, field, error):
        if isinstance(error,ValidationError) and hasattr(error,'error_list'):
            error = ValidationError([
                ValidationError(self.display_messages[item.code],code=item.code,params=item.params)
                if item.code in self.display_messages else item for item in error.error_list])
        return super().add_error(field,error)


class RecoveryEmailForm(forms.Form):
    email = forms.EmailField(label='Email đã đăng ký', max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete':'email'}))


class RecoveryLinkForm(forms.Form):
    uid = forms.CharField(max_length=64, widget=forms.HiddenInput)
    token = forms.CharField(max_length=128, widget=forms.HiddenInput)


def eligible(user):
    if not user or not user.is_active or user.is_staff or user.is_superuser or not user.has_usable_password():
        return False
    if not user.groups.filter(name='CUSTOMER').exists() or user.groups.filter(name__in=['STAFF','ADMIN']).exists():
        return False
    profile = CustomerProfile.objects.filter(user=user,email_verified_at__isnull=False).first()
    if not profile or profile.email != user.email.strip().lower():
        return False
    # Legacy auth emails were never globally unique: don't guess between accounts.
    return get_user_model().objects.annotate(recovery_email=Lower(Trim('email'))).filter(recovery_email=profile.email).count() == 1


def eligible_email(email):
    normalized = normalize_email(email)
    users = list(get_user_model().objects.annotate(recovery_email=Lower(Trim('email'))).filter(recovery_email=normalized)[:2])
    return users[0] if len(users)==1 and eligible(users[0]) else None


@transaction.atomic
def rate_budget(scope, identity, seconds, limit):
    # Hash direct-peer IP or canonical email; never store email/IP or trust XFF.
    digest = hashlib.sha256(str(identity).encode()).hexdigest()
    key = scope+':'+digest+':'+str(int(time.time())//seconds)
    bucket,_ = SubmissionLimit.objects.get_or_create(key=key)
    bucket = SubmissionLimit.objects.select_for_update().get(pk=bucket.pk)
    if bucket.count >= limit:
        return False
    bucket.count += 1
    bucket.save(update_fields=['count'])
    return True


def email_budget(email):
    return rate_budget('customer-reset-email',email.strip().lower(),60,1)


def ip_budget(request,scope,limit):
    return rate_budget(scope,request.META.get('REMOTE_ADDR',''),600,limit)


def send_recovery(email):
    """Internal status only; the public response never exposes this result."""
    if not enabled():
        return 'unavailable'
    if not email_budget(email):
        return 'throttled'
    user = eligible_email(email)
    if not user:
        return 'ineligible'
    if not email_ready():
        return 'unavailable'
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = settings.NAU_ACCOUNT_PUBLIC_ORIGIN.rstrip('/')+reverse('customer_password_reset_exchange')+'#uid='+uid+'&token='+token
    context = {'reset_url':url,'expiry_minutes':settings.PASSWORD_RESET_TIMEOUT//60}
    message = EmailMultiAlternatives('Nâu Coffee — đặt lại mật khẩu',
        render_to_string('emails/customer_password_reset.txt',context),settings.DEFAULT_FROM_EMAIL,[user.email.strip()])
    message.attach_alternative(render_to_string('emails/customer_password_reset.html',context),'text/html')
    try:
        return 'sent' if message.send(fail_silently=False)==1 else 'failed'
    except (smtplib.SMTPException,OSError):
        return 'failed'


def recovery_user(uid, *, lock=False):
    if not isinstance(uid,str) or len(uid)>64:
        return None
    try:
        pk = int(urlsafe_base64_decode(uid).decode())
        if not 0 < pk < 2**63:
            return None
    except (ValueError,TypeError,UnicodeError,OverflowError):
        return None
    queryset = get_user_model().objects
    if lock:
        queryset = queryset.select_for_update()
    user = queryset.filter(pk=pk).first()
    return user if eligible(user) else None


def private(response):
    response['Referrer-Policy'] = 'same-origin'
    return response


def clear_reset(session):
    session.pop(UID_KEY,None)
    session.pop(TOKEN_KEY,None)


@feature
@require_http_methods(['GET','POST'])
@sensitive_post_parameters('email')
def request_reset(request):
    form = RecoveryEmailForm(request.POST if request.method=='POST' else None)
    if request.method=='POST' and form.is_valid():
        # Same response for absent, pending, privileged, throttled or SMTP-failed users.
        if ip_budget(request,'customer-reset-ip',limit=5):
            send_recovery(form.cleaned_data['email'])
        return private(redirect('customer_password_reset_done'))
    return private(render(request,'registration/customer_password_reset_form.html',{'form':form}))


@feature
@require_GET
def reset_done(request):
    return private(render(request,'registration/customer_password_reset_done.html'))


@feature
@require_http_methods(['GET','POST'])
@sensitive_post_parameters('uid','token')
def exchange(request):
    if request.method=='GET':
        return private(render(request,'registration/customer_password_reset_exchange.html',{'link_form':RecoveryLinkForm()}))
    clear_reset(request.session)
    form = RecoveryLinkForm(request.POST)
    if form.is_valid() and ip_budget(request,'customer-reset-link',limit=20):
        user = recovery_user(form.cleaned_data['uid'])
        if user and default_token_generator.check_token(user,form.cleaned_data['token']):
            request.session.cycle_key()
            request.session[UID_KEY] = form.cleaned_data['uid']
            request.session[TOKEN_KEY] = form.cleaned_data['token']
            return private(redirect('customer_password_reset_confirm'))
    return private(render(request,'registration/customer_password_reset_confirm.html',{'validlink':False}))


@feature
@require_http_methods(['GET','POST'])
@sensitive_post_parameters('new_password1','new_password2','reset_uid')
def confirm(request):
    uid,token = request.session.get(UID_KEY,''),request.session.get(TOKEN_KEY,'')
    # Bind the rendered form to its account even when another tab exchanges a link.
    if request.method=='POST' and request.POST.get('reset_uid') != uid:
        return private(render(request,'registration/customer_password_reset_confirm.html',{'validlink':False}))
    # Recheck a fresh locked user and token at the actual password write. Concurrent
    # submissions cannot both consume the old password-derived Django token.
    with transaction.atomic():
        user = recovery_user(uid,lock=True)
        if not user or not default_token_generator.check_token(user,token):
            clear_reset(request.session)
            return private(render(request,'registration/customer_password_reset_confirm.html',{'validlink':False}))
        form = CustomerSetPasswordForm(user,request.POST if request.method=='POST' else None)
        if request.method=='POST' and form.is_valid():
            form.save()  # Django validators + set_password(); never auto-login.
            clear_reset(request.session)
            return private(redirect('customer_password_reset_complete'))
    return private(render(request,'registration/customer_password_reset_confirm.html',{'validlink':True,'form':form,'reset_uid':uid}))


@feature
@require_GET
def complete(request):
    return private(render(request,'registration/customer_password_reset_complete.html'))
