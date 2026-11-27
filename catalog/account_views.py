from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from support.services import allow_submission
from .models import Address


from .permissions import customer_required, internal_home, is_customer_user, is_internal_user


class RateLimitedLoginView(LoginView):
    rate_key = 'login'

    def post(self, request, *args, **kwargs):
        if not allow_submission(request, self.rate_key, limit=15):
            form = self.form_class(request=request, data={})
            form.add_error(None, 'Quá nhiều lần đăng nhập. Vui lòng thử lại sau 10 phút.')
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)


class LimitedLoginView(RateLimitedLoginView):
    """Public customer gateway; internal identities never receive a session here."""
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        if is_internal_user(request.user):
            return redirect(internal_home(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not is_customer_user(form.get_user()):
            form.add_error(None, 'Không thể đăng nhập tại cổng này. Vui lòng kiểm tra thông tin và thử lại.')
            return self.form_invalid(form)
        return super().form_valid(form)


class InternalLoginView(RateLimitedLoginView):
    template_name = 'registration/internal_login.html'
    rate_key = 'internal_login'

    def dispatch(self, request, *args, **kwargs):
        if is_internal_user(request.user):
            return redirect(internal_home(request.user))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if not is_internal_user(form.get_user()):
            form.add_error(None, 'Không thể đăng nhập tại cổng này. Vui lòng kiểm tra thông tin và thử lại.')
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        # Internal identities always start at their authoritative workspace;
        # do not let a supplied next value cross role boundaries.
        return internal_home(self.request.user)


@require_POST
def logout_view(request):
    destination = '/internal/login/' if is_internal_user(request.user) else '/'
    logout(request)
    return redirect(destination)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': 'Tên', 'last_name': 'Họ', 'email': 'Thư điện tử'}


class AddressForm(forms.ModelForm):
    phone = forms.CharField(label='Điện thoại', max_length=30,
        validators=[RegexValidator(r'^\+?[0-9]{8,15}$', 'Nhập 8–15 chữ số.')])

    class Meta:
        model = Address
        fields = ['label', 'recipient', 'phone', 'text']
        labels = {'label': 'Tên gợi nhớ', 'recipient': 'Người nhận', 'text': 'Địa chỉ mô phỏng'}
        widgets = {'text': forms.Textarea(attrs={'rows': 3})}


@customer_required
def profile(request):
    from .customer_accounts import enabled
    from .permissions import has_role
    if enabled() and has_role(request.user, 'CUSTOMER') and not has_role(request.user, 'STAFF', 'ADMIN'):
        from .customer_views import profile as customer_profile
        return customer_profile(request)
    form = ProfileForm(request.POST if request.method == 'POST' else None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Đã cập nhật hồ sơ.')
        return redirect('profile')
    return render(request, 'catalog/profile.html', {'form': form})


@customer_required
def addresses(request, pk=None):
    address = get_object_or_404(Address, pk=pk, user=request.user) if pk else None
    form = AddressForm(request.POST if request.method == 'POST' else None, instance=address)
    if request.method == 'POST' and form.is_valid():
        value = form.save(commit=False)
        value.user = request.user
        value.save()
        messages.success(request, 'Đã lưu địa chỉ mô phỏng. Phạm vi giao vẫn cần nhân viên xác minh.')
        return redirect('addresses')
    return render(request, 'catalog/addresses.html', {'form': form, 'addresses': request.user.addresses.order_by('pk')})


@customer_required
@require_POST
def remove_address(request, pk):
    get_object_or_404(Address, user=request.user, pk=pk).delete()
    return redirect('addresses')
