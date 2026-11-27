from functools import wraps
import secrets
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from support.services import allow_submission
from . import customer_accounts as accounts
from .customer_forms import (CustomerRegistrationForm, CustomerDetailsForm, CustomerContactForm,
                             LookupForm, ResendForm, ActivationForm, ConsentForm)
from .customer_models import CustomerProfile
from .permissions import roles_required

EMAIL_MESSAGES = {
    'sent': 'Dịch vụ email đã tiếp nhận yêu cầu. Vui lòng kiểm tra hộp thư để xác minh.',
    'unavailable': 'Dịch vụ gửi email chưa sẵn sàng. Tài khoản vẫn chờ xác minh; vui lòng thử gửi lại khi dịch vụ hoạt động.',
    'failed': 'Chưa gửi được email. Thông tin đã được giữ nguyên; vui lòng dùng chức năng gửi lại.',
    'throttled': 'Vui lòng chờ ít nhất một phút trước khi gửi lại.',
    'not_pending': 'Tài khoản không có yêu cầu xác minh đang chờ.',
}


def feature(view):
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not accounts.enabled():
            raise Http404
        return view(request, *args, **kwargs)
    return never_cache(guarded)


def add_errors(form, error):
    if isinstance(error, IntegrityError):
        form.add_error(None, 'Số điện thoại, email hoặc tên đăng nhập đã được sử dụng. Không tạo tài khoản trùng.')
    elif hasattr(error, 'message_dict'):
        for key, values in error.message_dict.items():
            for value in values:
                form.add_error(key if key in form.fields else None, value)
    else:
        for value in error.messages:
            form.add_error(None, value)


@feature
@sensitive_post_parameters()
def register(request):
    if request.user.is_authenticated:
        return redirect('profile')
    form = CustomerRegistrationForm(request.POST if request.method == 'POST' else None, request=request)
    if request.method == 'POST':
        if not allow_submission(request, 'customer-register', limit=10):
            return render(request, 'registration/customer_register.html', {'form': form}, status=429)
        if form.is_valid():
            try:
                from support import policies
                profile = policies.register_customer(request, form.cleaned_data) if policies.enabled() else accounts.create_customer(form.cleaned_data)
            except (ValidationError, IntegrityError) as error:
                add_errors(form, error)
            else:
                state = accounts.send_activation(profile.user_id)
                return render(request, 'registration/customer_pending.html', {'delivery_message': EMAIL_MESSAGES[state]})
    return render(request, 'registration/customer_register.html', {'form': form})


@feature
@sensitive_post_parameters('token', 'new_password1', 'new_password2')
def activate(request):
    form = ActivationForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST':
        if not allow_submission(request, 'customer-activate', limit=20):
            return render(request, 'registration/customer_activate.html', {'form': form}, status=429)
        if form.is_valid():
            try:
                activated = accounts.activate(form.cleaned_data['token'], form.cleaned_data['new_password1'], form.cleaned_data['new_password2'])
            except (ValidationError, IntegrityError) as error:
                add_errors(form, error)
            else:
                return render(request, 'registration/customer_activated.html', {'login_username': activated.user.username})
    return render(request, 'registration/customer_activate.html', {'form': form})


@feature
def resend(request):
    form = ResendForm(request.POST if request.method == 'POST' else None)
    result = ''
    if request.method == 'POST':
        if not allow_submission(request, 'customer-resend', limit=5):
            return render(request, 'registration/customer_resend.html', {'form': form}, status=429)
        if form.is_valid():
            if not accounts.email_ready():
                result = EMAIL_MESSAGES['unavailable']
            else:
                profile = CustomerProfile.objects.filter(email__iexact=form.cleaned_data['email'].strip()).first()
                if profile and not profile.email_verified_at:
                    accounts.send_activation(profile.user_id)
                # Same response for known, unknown, active and pending identities.
                result = 'Nếu tài khoản có yêu cầu xác minh phù hợp, hệ thống đã xử lý yêu cầu gửi lại. Nếu chưa nhận được thư, hãy chờ một phút rồi thử lại hoặc liên hệ hỗ trợ.'
    return render(request, 'registration/customer_resend.html', {'form': form, 'delivery_message': result})


@feature
@login_required
@sensitive_post_parameters('current_password')
def profile(request):
    current = CustomerProfile.objects.filter(user=request.user).first()
    initial = {'full_name': current.full_name if current else request.user.get_full_name(),
               'phone': current.phone if current else '', 'email': current.email if current else request.user.email}
    form = CustomerContactForm(request.POST if request.method == 'POST' else None, user=request.user, initial=initial)
    result = ''
    if request.method == 'POST':
        if not allow_submission(request, 'customer-contact', limit=5):
            return render(request, 'catalog/customer_profile.html', {'form': form, 'profile': current}, status=429)
        if form.is_valid():
            try:
                current = accounts.request_contact_change(request.user, form.cleaned_data)
            except (ValidationError, IntegrityError) as error:
                add_errors(form, error)
            else:
                result = EMAIL_MESSAGES[accounts.send_activation(request.user.pk)]
    return render(request, 'catalog/customer_profile.html', {'form': form, 'profile': current,
        'delivery_message': result, 'consent_form': ConsentForm()})


@feature
@login_required
@require_POST
@sensitive_post_parameters('current_password')
def counter_consent(request):
    form = ConsentForm(request.POST)
    code = ''
    if not allow_submission(request, 'customer-counter-code', limit=5):
        return render(request, 'catalog/customer_consent.html', {'form': form}, status=429)
    if form.is_valid():
        try:
            code = accounts.issue_counter_consent(request.user, form.cleaned_data['current_password'])
        except ValidationError as error:
            add_errors(form, error)
    return render(request, 'catalog/customer_consent.html', {'form': form, 'code': code})


@feature
@roles_required('STAFF', 'ADMIN')
@sensitive_post_parameters()
def lookup(request):
    form = LookupForm(request.POST if request.method == 'POST' else None)
    found = None
    selection = ''
    addresses = []
    searched = False
    if request.method == 'POST':
        if not allow_submission(request, 'staff-customer-lookup', limit=20):
            return render(request, 'commerce/customer_lookup.html', {'form': form}, status=429)
        if form.is_valid():
            searched = True
            found = CustomerProfile.objects.select_related('user').filter(phone=form.cleaned_data['phone'],
                user__groups__name='CUSTOMER', user__is_staff=False, user__is_superuser=False).exclude(
                user__groups__name__in=['STAFF', 'ADMIN']).first()
            if found:
                context = request.session.setdefault('counter_selection_context', secrets.token_urlsafe(24))
                selection = accounts.selection_for(found, request.user, session_context=context)
                if form.cleaned_data['include_addresses']:
                    addresses = found.user.addresses.order_by('pk')[:5]
                request.session['counter_customer_name'] = found.full_name
                request.session['counter_customer_selection'] = selection
                request.session['counter_customer_phone'] = found.phone
            else:
                request.session.pop('counter_customer_name', None)
                request.session.pop('counter_customer_selection', None)
                request.session.pop('counter_customer_phone', None)
    return render(request, 'commerce/customer_lookup.html', {'form': form, 'customer_profile': found,
        'selection': selection, 'addresses': addresses, 'searched': searched})


@feature
@roles_required('STAFF', 'ADMIN')
@sensitive_post_parameters()
def staff_create(request):
    form = CustomerDetailsForm(request.POST if request.method == 'POST' else None)
    result = ''
    created = False
    if request.method == 'POST':
        if not allow_submission(request, 'staff-customer-create', limit=5):
            return render(request, 'commerce/customer_create.html', {'form': form}, status=429)
        if form.is_valid():
            try:
                profile = accounts.create_customer(form.cleaned_data, actor=request.user)
            except (ValidationError, IntegrityError) as error:
                add_errors(form, error)
            else:
                created = True
                result = EMAIL_MESSAGES[accounts.send_activation(profile.user_id)]
                form = CustomerDetailsForm()
    return render(request, 'commerce/customer_create.html', {'form': form, 'created': created, 'delivery_message': result})


@feature
@roles_required('STAFF', 'ADMIN')
@require_POST
def staff_resend(request, pk):
    if not allow_submission(request, 'staff-customer-resend', limit=5):
        return render(request, 'commerce/customer_create.html', {'delivery_message': 'Đã đạt giới hạn gửi lại.'}, status=429)
    profile = get_object_or_404(CustomerProfile, pk=pk, user__groups__name='CUSTOMER', user__is_staff=False, user__is_superuser=False)
    result = accounts.send_activation(profile.user_id)
    return render(request, 'commerce/customer_create.html', {'delivery_message': EMAIL_MESSAGES[result]})


@feature
@roles_required('STAFF', 'ADMIN')
@require_POST
def clear_selection(request):
    for key in ('counter_customer_selection', 'counter_customer_phone', 'counter_customer_name', 'counter_selection_context'):
        request.session.pop(key, None)
    return redirect('new_manual')
