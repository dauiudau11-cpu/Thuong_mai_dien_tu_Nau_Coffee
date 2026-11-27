from django import forms
from django.forms import formset_factory, BaseFormSet
from catalog.models import ProductVariant, ProductOption
from .models import Ingredient


class ManualOrderForm(forms.Form):
    customer_selection = forms.CharField(required=False, widget=forms.HiddenInput, max_length=1024)
    customer_consent = forms.CharField(label='Mã đồng ý dùng một lần của khách', required=False, max_length=100, widget=forms.PasswordInput)
    confirm_customer = forms.BooleanField(label='Tôi đã kiểm tra và xác nhận đúng khách hàng', required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .vouchers import enabled as vouchers_enabled
        if vouchers_enabled():
            self.fields['voucher'] = forms.CharField(label='Chọn voucher sau khi xác minh khách',required=False,
                max_length=11,widget=forms.Select(choices=[('', 'Không dùng voucher')]))
        from catalog.customer_accounts import enabled
        if not enabled():
            for key in ('customer_selection', 'customer_consent', 'confirm_customer'):
                self.fields.pop(key)

    def clean(self):
        values=super().clean()
        if self.data.get('voucher_code') or (hasattr(self.data,'getlist') and len(self.data.getlist('voucher'))>1):
            raise forms.ValidationError('Chỉ chọn một voucher từ danh sách.')
        return values

    channel = forms.ChoiceField(label='Kênh nhập tay', choices=[('COUNTER', 'Tại quầy'), ('APP', 'Ứng dụng bên ngoài')])
    customer_name = forms.CharField(label='Tên khách hàng', max_length=150)
    phone = forms.CharField(label='Điện thoại (không bắt buộc)', required=False, max_length=30)
    external_reference = forms.CharField(label='Mã tham chiếu ngoài (bắt buộc với APP)', required=False, max_length=100)
    scheduled_for = forms.DateTimeField(label='Lịch nhận (giờ Việt Nam)', required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'step': 900}), input_formats=['%Y-%m-%dT%H:%M'])
    notes = forms.CharField(label='Ghi chú', required=False, max_length=500, widget=forms.Textarea(attrs={'rows': 2}))
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput)


class ManualLineForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from catalog.approved_menu import enabled
        if enabled():
            self.fields['variant'].queryset = self.fields['variant'].queryset.filter(size='FIXED')
            self.fields['options'].queryset = ProductOption.objects.none()
            self.fields['options'].widget = forms.MultipleHiddenInput()

    variant = forms.ModelChoiceField(label='Món / cỡ ly', queryset=ProductVariant.objects.filter(
        is_available=True, product__is_active=True, product__category__is_active=True).select_related('product'))
    quantity = forms.IntegerField(label='Số lượng', min_value=1, max_value=99)
    options = forms.ModelMultipleChoiceField(label='Tùy chọn (phải thuộc món)', required=False,
        queryset=ProductOption.objects.filter(is_active=True).select_related('product'))


class ManualLineSet(BaseFormSet):
    def clean(self):
        super().clean()
        if not self.is_bound or not self.management_form.is_valid():
            return
        count = self.management_form.cleaned_data['TOTAL_FORMS']
        indexes = {str(i) for i in range(min(count, 10))}
        management = {self.add_prefix(name) for name in ('TOTAL_FORMS','INITIAL_FORMS','MIN_NUM_FORMS','MAX_NUM_FORMS')}
        for key in self.data:
            if key.startswith(self.prefix + '-') and key not in management:
                token = key[len(self.prefix) + 1:].split('-', 1)[0]
                if token not in indexes:
                    raise forms.ValidationError('Chỉ số dòng món không khớp TOTAL_FORMS. Chưa tạo đơn; hãy kiểm tra các dòng đã nhập.')



ManualLines = formset_factory(ManualLineForm, formset=ManualLineSet, extra=3,
    min_num=1, max_num=10, absolute_max=10, validate_min=True, validate_max=True, can_delete=True)


class StockForm(forms.Form):
    ingredient = forms.ModelChoiceField(label='Nguyên liệu', queryset=Ingredient.objects.filter(is_active=True))
    delta = forms.DecimalField(label='Biến động (+ nhập, − xuất)', max_digits=12, decimal_places=3)
    reason = forms.ChoiceField(label='Loại', choices=[('PURCHASE', 'Nhập kho'), ('ADJUST', 'Điều chỉnh'), ('WASTE', 'Hao hụt')])
    note = forms.CharField(label='Lý do bắt buộc', max_length=300)
    key = forms.UUIDField(widget=forms.HiddenInput)


class DeliveryForm(forms.Form):
    distance = forms.DecimalField(label='Khoảng cách nhân viên đã xác minh (km)', min_value=0, max_value=3, decimal_places=2)
    reason = forms.CharField(label='Căn cứ xác minh thủ công', max_length=250)


class ReportForm(forms.Form):
    start = forms.DateField(label='Từ ngày', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    end = forms.DateField(label='Đến ngày', required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    def clean(self):
        values=super().clean()
        if self.data.get('voucher_code') or (hasattr(self.data,'getlist') and len(self.data.getlist('voucher'))>1):
            raise forms.ValidationError('Chỉ chọn một voucher từ danh sách.')
        return values

    channel = forms.ChoiceField(label='Kênh', required=False, choices=[('', 'Tất cả'), ('WEB', 'Website'), ('COUNTER', 'Quầy'), ('APP', 'Ứng dụng')])

    def clean(self):
        values = super().clean()
        if values.get('start') and values.get('end') and values['end'] < values['start']:
            raise forms.ValidationError('Ngày kết thúc phải sau ngày bắt đầu.')
        return values
