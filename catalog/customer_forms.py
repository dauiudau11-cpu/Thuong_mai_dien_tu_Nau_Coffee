from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .customer_accounts import validate_identity, normalize_phone


def clean_identity(form, values):
    if all(values.get(k) for k in ('full_name', 'phone', 'email')):
        try:
            values['full_name'], values['phone'], values['email'] = validate_identity(
                values['full_name'], values['phone'], values['email'], user_id=getattr(form, 'identity_user_id', None))
        except ValidationError as error:
            for field, errors in error.message_dict.items():
                for message in errors:
                    form.add_error(field, message)
    return values


class CustomerRegistrationForm(UserCreationForm):
    full_name = forms.CharField(label='Họ và tên', min_length=2, max_length=150)
    phone = forms.CharField(label='Số điện thoại', max_length=30, widget=forms.TextInput(attrs={'inputmode': 'tel', 'autocomplete': 'tel'}))
    email = forms.EmailField(label='Email', max_length=254, widget=forms.EmailInput(attrs={'autocomplete': 'email'}))
    field_order = ['full_name', 'phone', 'email', 'username', 'password1', 'password2']

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        from support.policies import add_fields
        add_fields(self, request, 'register')
        self.fields['username'].widget.attrs.pop('autofocus', None)
        self.fields['full_name'].widget.attrs['autocomplete'] = 'name'

    def clean(self):
        from support.policies import clean_form
        return clean_form(self, clean_identity(self, super().clean()))


class CustomerDetailsForm(forms.Form):
    full_name = forms.CharField(label='Họ và tên', min_length=2, max_length=150)
    phone = forms.CharField(label='Số điện thoại chính', max_length=30, widget=forms.TextInput(attrs={'inputmode': 'tel', 'autocomplete': 'tel'}))
    email = forms.EmailField(label='Email', max_length=254, widget=forms.EmailInput(attrs={'autocomplete': 'email'}))

    def __init__(self, *args, user=None, **kwargs):
        self.identity_user_id = user.pk if user else None
        super().__init__(*args, **kwargs)

    def clean(self):
        return clean_identity(self, super().clean())


class CustomerContactForm(CustomerDetailsForm):
    current_password = forms.CharField(label='Mật khẩu hiện tại', widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))


class LookupForm(forms.Form):
    phone = forms.CharField(label='Số điện thoại khách', max_length=30, widget=forms.TextInput(attrs={'inputmode': 'tel'}))
    include_addresses = forms.BooleanField(label='Hiện địa chỉ đã lưu khi cần', required=False)

    def clean_phone(self):
        return normalize_phone(self.cleaned_data['phone'])


class ResendForm(forms.Form):
    email = forms.EmailField(label='Email đăng ký', max_length=254)


class ConsentForm(forms.Form):
    current_password = forms.CharField(label='Xác nhận mật khẩu hiện tại', widget=forms.PasswordInput)


class ActivationForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput, max_length=1024)
    new_password1 = forms.CharField(label='Mật khẩu mới (tài khoản chờ kích hoạt)', required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
    new_password2 = forms.CharField(label='Xác nhận mật khẩu mới', required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))
