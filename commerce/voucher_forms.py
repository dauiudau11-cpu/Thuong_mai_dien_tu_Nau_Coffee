"""Voucher form declarations shared by quote compatibility and Admin views.

Keep legacy grant eligibility separate from verified_customers(): the unified
editor applies its stricter verified-profile rule in the service layer.
"""
from django import forms
from django.contrib.auth import get_user_model
from .models import Voucher, VoucherCampaign


class CampaignForm(forms.ModelForm):
    audience = forms.ChoiceField(label='Chính sách campaign mới', choices=VoucherCampaign._meta.get_field('audience').choices)

    class Meta:
        model = Voucher
        fields = ['code', 'kind', 'amount', 'cap', 'min_subtotal', 'max_uses', 'starts_at', 'ends_at', 'is_active', 'allow_sale_stacking']
        labels = {'code': 'Tên voucher', 'kind': 'Cách giảm', 'amount': 'Mức giảm', 'cap': 'Giảm tối đa (đ)', 'min_subtotal': 'Đơn tối thiểu (đ)', 'max_uses': 'Tổng lượt campaign', 'starts_at': 'Bắt đầu', 'ends_at': 'Kết thúc', 'is_active': 'Đang mở', 'allow_sale_stacking': 'Cộng dồn giá khuyến mại'}
        widgets = {key: forms.DateTimeInput(attrs={'type': 'datetime-local'}) for key in ('starts_at', 'ends_at')}

class GrantForm(forms.Form):
    campaign = forms.ModelChoiceField(label='Campaign riêng', queryset=VoucherCampaign.objects.none())
    user = forms.ModelChoiceField(label='Tài khoản khách hàng', queryset=get_user_model().objects.none())
    extra = forms.IntegerField(label='Số lượt cấp thêm', min_value=1, max_value=100000)
    reason = forms.CharField(label='Lý do cấp', max_length=250)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['campaign'].queryset = VoucherCampaign.objects.filter(audience='PRIVATE').select_related('voucher')
        self.fields['campaign'].label_from_instance = lambda obj: obj.voucher.code
        self.fields['user'].queryset = (
            get_user_model().objects.filter(
                is_active=True, is_staff=False, is_superuser=False, groups__name='CUSTOMER'
            ).exclude(groups__name__in=['STAFF', 'ADMIN']).exclude(
                customer_profile__origin__in=['PUBLIC', 'STAFF'],
                customer_profile__email_verified_at__isnull=True,
            ).distinct()
        )
