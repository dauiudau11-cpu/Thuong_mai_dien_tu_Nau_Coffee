"""Customer identity services. Writes are opt-in and transactional; never infer from orders."""
from datetime import timedelta
import re
import secrets
import smtplib
import uuid
from email.utils import parseaddr
from urllib.parse import urlsplit
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.validators import validate_email
from django.db import transaction
from django.db.models.functions import Lower, Trim
from django.utils import timezone
from .customer_models import CustomerProfile, CounterConsent
from .permissions import has_role

ACTIVATION_SALT = 'nau.customer.activation.v1'
SELECTION_SALT = 'nau.counter.selection.v2'
COUNTER_SELECTION_PURPOSE = 'COUNTER_CUSTOMER_LINK'


def enabled():
    return settings.NAU_CUSTOMER_ACCOUNTS_ENABLED


def require_enabled():
    if not enabled():
        raise ValidationError('Tính năng tài khoản mới chưa được mở; cần duyệt migration và email trước.')


def normalize_phone(value):
    value = str(value).strip()
    if not re.fullmatch(r'[+0-9 ()-]+', value, flags=re.ASCII):
        raise ValidationError('Nhập số điện thoại Việt Nam hợp lệ.')
    value = re.sub(r'[ ()-]', '', value)
    if value.startswith('0084'):
        value = '0' + value[4:]
    elif value.startswith('+84'):
        value = '0' + value[3:]
    if not re.fullmatch(r'(?:0[35789][0-9]{8}|02[0-9]{9})', value, flags=re.ASCII):
        raise ValidationError('Nhập số di động 10 chữ số hoặc số cố định Việt Nam 11 chữ số.')
    return '+84' + value[1:]


def normalize_email(value):
    value = str(value).strip().lower()
    if len(value) > 254:
        raise ValidationError('Email tối đa 254 ký tự.')
    validate_email(value)
    return value


def validate_identity(full_name, phone, email, *, user_id=None):
    name = full_name.strip()
    if not 2 <= len(name) <= 150 or any(ord(c) < 32 for c in name):
        raise ValidationError({'full_name': 'Họ tên cần 2–150 ký tự, không chứa ký tự điều khiển.'})
    errors = {}
    for key, normalize, value in [('phone', normalize_phone, phone), ('email', normalize_email, email)]:
        try:
            errors[key] = normalize(value)
        except ValidationError as error:
            raise ValidationError({key: error.messages}) from None
    phone, email = errors['phone'], errors['email']
    if CustomerProfile.objects.exclude(user_id=user_id).filter(phone=phone).exists():
        raise ValidationError({'phone': 'Số điện thoại đã thuộc một tài khoản. Không tạo bản sao.'})
    if (CustomerProfile.objects.exclude(user_id=user_id).filter(email__iexact=email).exists()
            or get_user_model().objects.exclude(pk=user_id).annotate(canonical_contact=Lower(Trim('email'))).filter(canonical_contact=email).exists()):
        raise ValidationError({'email': 'Email đã được sử dụng. Vui lòng đăng nhập hoặc liên hệ hỗ trợ.'})
    return name, phone, email


@transaction.atomic
def create_customer(data, *, actor=None):
    require_enabled()
    if actor is not None and not has_role(actor, 'STAFF', 'ADMIN'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    name, phone, email = validate_identity(data['full_name'], data['phone'], data['email'])
    username = ('khach_' + uuid.uuid4().hex) if actor else data['username']
    user = get_user_model()(username=username, first_name=name, email=email, is_active=False,
                            is_staff=False, is_superuser=False)
    if actor:
        user.set_unusable_password()
    else:
        from django.contrib.auth.password_validation import validate_password
        validate_password(data['password1'], user)
        user.set_password(data['password1'])
    user.full_clean()
    user.save()
    from django.contrib.auth.models import Group
    user.groups.add(Group.objects.get_or_create(name='CUSTOMER')[0])
    return CustomerProfile.objects.create(user=user, full_name=name, phone=phone, email=email,
        origin='STAFF' if actor else 'PUBLIC', created_by=actor)


def email_ready():
    """Only explicit sandbox may use loopback; real mail requires public HTTPS."""
    try:
        origin = urlsplit(settings.NAU_ACCOUNT_PUBLIC_ORIGIN)
        origin.port  # Validate malformed port without connecting or resolving DNS.
        validate_email(parseaddr(settings.DEFAULT_FROM_EMAIL)[1])
    except (ValueError, ValidationError):
        return False
    smtp = settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend'
    sandbox = settings.NAU_ACCOUNT_ALLOW_TEST_EMAIL and (
        settings.EMAIL_BACKEND == 'django.core.mail.backends.locmem.EmailBackend'
        or (smtp and settings.EMAIL_HOST in ('127.0.0.1','localhost')))
    valid_origin = (origin.hostname and not origin.username and not origin.password
        and not origin.query and not origin.fragment and origin.path in ('','/'))
    if not settings.NAU_ACCOUNT_EMAIL_READY or not valid_origin:
        return False
    if sandbox:
        return origin.scheme == 'https' or (settings.DEBUG and origin.scheme == 'http'
                and origin.hostname in ('127.0.0.1','localhost'))
    import ipaddress
    host = origin.hostname.lower().rstrip('.')
    try:
        ipaddress.ip_address(host)
        public_host = False  # A configured public DNS name is required for customer links.
    except ValueError:
        public_host = '.' in host and host not in ('localhost','localhost.localdomain') and not host.endswith(('.localhost','.local','.invalid','.test','.example'))
    password = settings.EMAIL_HOST_PASSWORD.replace(' ','')
    return bool(origin.scheme == 'https' and public_host and smtp
        and settings.EMAIL_HOST == 'smtp.gmail.com' and settings.EMAIL_PORT == 587
        and settings.EMAIL_USE_TLS and not settings.EMAIL_USE_SSL and settings.EMAIL_TIMEOUT == 15
        and settings.EMAIL_HOST_USER == 'naucoffee.official@gmail.com'
        and parseaddr(settings.DEFAULT_FROM_EMAIL)[1] == settings.EMAIL_HOST_USER
        and len(password) == 16 and password.isascii() and password.isalnum())


def token_for(profile):
    kind = 'activate' if not profile.user.is_active and not profile.email_verified_at and profile.origin != 'LEGACY' else 'contact'
    return signing.dumps({'uid': profile.user_id, 'nonce': str(profile.activation_nonce), 'kind': kind}, salt=ACTIVATION_SALT)


def send_activation(user_id):
    require_enabled()
    if not email_ready():
        return 'unavailable'
    with transaction.atomic():
        profile = CustomerProfile.objects.select_for_update(of=('self',)).select_related('user').get(user_id=user_id)
        if profile.email_verified_at and not profile.pending_email:
            return 'not_pending'
        now = timezone.now()
        if profile.last_email_attempt and now - profile.last_email_attempt < timedelta(seconds=settings.NAU_ACCOUNT_EMAIL_COOLDOWN):
            return 'throttled'
        profile.activation_nonce = uuid.uuid4()
        profile.last_email_attempt = now
        profile.save(update_fields=['activation_nonce', 'last_email_attempt'])
        from django.urls import reverse
        # Fragment never reaches HTTP access logs. Only the customer mail receives it.
        url = settings.NAU_ACCOUNT_PUBLIC_ORIGIN.rstrip('/') + reverse('customer_activate') + '#token=' + token_for(profile)
        recipient = profile.pending_email or profile.email
    try:
        context = {'activation_url': url, 'username': profile.user.username,
            'invitation': profile.origin == 'STAFF' and not profile.email_verified_at,
            'expiry_hours': settings.NAU_ACCOUNT_ACTIVATION_TIMEOUT // 3600}
        message = EmailMultiAlternatives(
            'Nâu Coffee — mời thiết lập tài khoản' if context['invitation'] else 'Nâu Coffee — xác minh tài khoản',
            render_to_string('emails/customer_activation.txt', context), settings.DEFAULT_FROM_EMAIL, [recipient])
        message.attach_alternative(render_to_string('emails/customer_activation.html', context),'text/html')
        sent = message.send(fail_silently=False)
    except (smtplib.SMTPException, OSError):
        return 'failed'
    return 'sent' if sent == 1 else 'failed'


def read_activation(token):
    try:
        payload = signing.loads(token, salt=ACTIVATION_SALT, max_age=settings.NAU_ACCOUNT_ACTIVATION_TIMEOUT)
        if (not isinstance(payload, dict) or payload.get('kind') not in ('activate', 'contact')
                or type(payload.get('uid')) is not int or payload['uid'] <= 0
                or not isinstance(payload.get('nonce'), str)):
            raise ValueError
        return payload
    except (signing.BadSignature, ValueError, TypeError):
        raise ValidationError('Liên kết không hợp lệ hoặc đã hết hạn. Vui lòng yêu cầu gửi lại.') from None


@transaction.atomic
def activate(token, password1='', password2=''):
    require_enabled()
    payload = read_activation(token)
    user = get_user_model().objects.select_for_update().filter(pk=payload['uid']).first()
    profile = CustomerProfile.objects.select_for_update().filter(user_id=payload['uid']).first()
    if not profile or str(profile.activation_nonce) != payload.get('nonce'):
        raise ValidationError('Liên kết đã sử dụng hoặc không còn hợp lệ.')
    if payload['kind'] == 'activate':
        if user.is_active or profile.email_verified_at or profile.origin == 'LEGACY':
            raise ValidationError('Liên kết không còn hợp lệ.')
        from django.contrib.auth.forms import SetPasswordForm
        form = SetPasswordForm(user, {'new_password1': password1, 'new_password2': password2})
        if not form.is_valid():
            raise ValidationError([message for errors in form.errors.values() for message in errors])
        user.set_password(form.cleaned_data['new_password1'])
        user.is_active = True
    elif not user.is_active:
        raise ValidationError('Tài khoản hiện không được phép cập nhật thông tin.')
    name, phone, email = validate_identity(profile.pending_full_name or profile.full_name,
        profile.pending_phone or profile.phone, profile.pending_email or profile.email, user_id=user.pk)
    profile.full_name, profile.phone, profile.email = name, phone, email
    profile.pending_email = profile.pending_phone = profile.pending_full_name = ''
    profile.email_verified_at = timezone.now()
    profile.activation_nonce = uuid.uuid4()  # Consume once, under the same row lock.
    profile.save()
    CounterConsent.objects.filter(user=user).update(used_at=timezone.now())
    user.first_name, user.last_name, user.email = name, '', email
    user.save(update_fields=['first_name', 'last_name', 'email', 'password', 'is_active'])
    return profile


@transaction.atomic
def request_contact_change(user, data):
    require_enabled()
    locked = get_user_model().objects.select_for_update().get(pk=user.pk)
    if not locked.check_password(data['current_password']):
        raise ValidationError('Mật khẩu hiện tại không đúng.')
    name, phone, email = validate_identity(data['full_name'], data['phone'], data['email'], user_id=user.pk)
    profile = CustomerProfile.objects.select_for_update().filter(user=user).first()
    if not profile:
        # Legacy stays active; no history/order-derived backfill or password reset.
        profile = CustomerProfile.objects.create(user=user, full_name=name, phone=phone, email=email, origin='LEGACY')
    profile.pending_full_name, profile.pending_phone, profile.pending_email = name, phone, email
    profile.activation_nonce = uuid.uuid4()
    profile.save()
    return profile


@transaction.atomic
def issue_counter_consent(user, password):
    require_enabled()
    # User lock also serializes concurrent issuance when no consent row exists yet.
    user = get_user_model().objects.select_for_update().get(pk=user.pk)
    if not user.check_password(password) or not has_role(user, 'CUSTOMER') or has_role(user, 'STAFF', 'ADMIN'):
        raise ValidationError('Cần đăng nhập tài khoản khách hàng và xác nhận mật khẩu hiện tại.')
    if not CustomerProfile.objects.filter(user=user, email_verified_at__isnull=False).exists():
        raise ValidationError('Vui lòng xác minh email trước khi nhận diện tại quầy.')
    code = secrets.token_urlsafe(9)
    CounterConsent.objects.update_or_create(user=user, defaults={'code_hash': make_password(code),
        'expires_at': timezone.now() + timedelta(minutes=5), 'used_at': None})
    return code


def selection_for(profile, actor, *, session_context):
    if not isinstance(session_context, str) or not session_context:
        raise ValidationError('Cần phiên tra cứu hợp lệ để chọn khách hàng.')
    return signing.dumps({'uid': profile.user_id, 'phone': profile.phone, 'actor': actor.pk,
        'session': session_context, 'purpose': COUNTER_SELECTION_PURPOSE}, salt=SELECTION_SALT)


def confirm_counter_customer(actor, data, *, consume=True):
    """Caller owns order transaction. Never accept a bare customer ID or phone."""
    supplied = any(data.get(k) for k in ('customer_selection', 'customer_consent', 'confirm_customer'))
    if not supplied:
        if data.get('customer_id') or data.get('user_id'):
            raise ValidationError('Không nhận mã tài khoản do request tự chỉ định.')
        return None
    require_enabled()
    if data['channel'] != 'COUNTER' or data.get('confirm_customer') is not True:
        raise ValidationError('Chỉ liên kết đơn COUNTER khi xác nhận đúng khách hàng.')
    try:
        selected = signing.loads(data.get('customer_selection', ''), salt=SELECTION_SALT, max_age=300)
        context = data.get('customer_selection_context')
        if (not isinstance(selected, dict) or type(selected.get('uid')) is not int
                or selected.get('purpose') != COUNTER_SELECTION_PURPOSE
                or not isinstance(context, str) or not context
                or not isinstance(selected.get('session'), str)
                or not secrets.compare_digest(selected['session'], context)):
            raise ValidationError('Lựa chọn không thuộc phiên hoặc mục đích nhập đơn hiện tại.')
        get_user_model().objects.select_for_update().get(pk=selected['uid'])
        profile = CustomerProfile.objects.select_for_update(of=('self',)).select_related('user').get(user_id=selected['uid'])
    except (signing.BadSignature, CustomerProfile.DoesNotExist, get_user_model().DoesNotExist, KeyError, TypeError, ValueError):
        raise ValidationError('Lựa chọn khách đã hết hạn hoặc không hợp lệ. Hãy tra cứu lại.') from None
    if (selected.get('actor') != actor.pk or selected.get('phone') != profile.phone
            or normalize_phone(data.get('phone', '')) != profile.phone or not profile.email_verified_at
            or not has_role(profile.user, 'CUSTOMER') or has_role(profile.user, 'STAFF', 'ADMIN')):
        raise ValidationError('Thông tin khách không khớp hoặc tài khoản chưa xác minh. Không liên kết.')
    proof = CounterConsent.objects.select_for_update().filter(user=profile.user).first()
    if (not proof or proof.used_at or proof.expires_at <= timezone.now()
            or not check_password(data.get('customer_consent', ''), proof.code_hash)):
        raise ValidationError('Mã đồng ý của khách không hợp lệ, hết hạn hoặc đã dùng.')
    if consume:
        proof.used_at = timezone.now()
        proof.save(update_fields=['used_at'])
    return profile
