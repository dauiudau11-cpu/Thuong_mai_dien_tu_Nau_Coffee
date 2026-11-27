from django import forms
from django.core.validators import RegexValidator
from django.utils import timezone


HOUR_CHOICES = [('', 'Giờ')] + [(f'{value:02d}', f'{value:02d}') for value in range(24)]
MINUTE_CHOICES = [('', 'Phút')] + [(f'{value:02d}', f'{value:02d}') for value in range(60)]


def clean_schedule_parts(form, values):
    parts = [values.get('scheduled_date'), values.get('scheduled_hour'), values.get('scheduled_minute')]
    if not any(part not in (None, '') for part in parts):
        values['scheduled_for'] = None
        return values
    if any(part in (None, '') for part in parts):
        form.add_error('scheduled_date', 'Vui lòng chọn đầy đủ ngày, giờ và phút nhận món.')
        values['scheduled_for'] = None
        return values
    selected = timezone.datetime.combine(
        values['scheduled_date'],
        timezone.datetime.min.time().replace(
            hour=int(values['scheduled_hour']), minute=int(values['scheduled_minute'])
        ),
    )
    values['scheduled_for'] = timezone.make_aware(selected, timezone.get_current_timezone())
    return values


class AddItemForm(forms.Form):
    variant = forms.IntegerField(min_value=1)
    quantity = forms.IntegerField(min_value=1, max_value=99)


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(label='Tên người nhận', max_length=150)
    phone = forms.CharField(label='Số điện thoại', max_length=30,
        validators=[RegexValidator(r'^\+?[0-9]{8,15}$', 'Số điện thoại gồm 8–15 chữ số.')])
    fulfillment = forms.ChoiceField(label='Phương thức nhận', choices=[('PICKUP', 'Nhận tại quán')], initial='PICKUP')
    payment_method = forms.ChoiceField(label='Phương thức thanh toán',
        choices=[('MOCK_ONLINE', 'Thanh toán trực tuyến mô phỏng')], initial='MOCK_ONLINE')
    voucher_code = forms.CharField(label='Mã giảm giá', max_length=30, required=False)
    scheduled_date = forms.DateField(label='Ngày nhận món', required=False,
        input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    scheduled_hour = forms.ChoiceField(label='Giờ nhận món', required=False, choices=HOUR_CHOICES)
    scheduled_minute = forms.ChoiceField(label='Phút nhận món', required=False, choices=MINUTE_CHOICES)
    notes = forms.CharField(label='Ghi chú', max_length=500, required=False, widget=forms.Textarea(attrs={'rows': 2}))
    idempotency_key = forms.UUIDField(widget=forms.HiddenInput)
    accept_demo = forms.BooleanField(label='Tôi hiểu đây là đặt hàng/thanh toán mô phỏng, không thu tiền thật.')

    def __init__(self, *args, user=None, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        from support.policies import add_fields
        add_fields(self, request, 'checkout')
        from .vouchers import enabled, available
        if enabled():
            self.fields.pop('voucher_code')
            self.fields['voucher'] = forms.ChoiceField(label='Chọn voucher', required=False,
                choices=[('', 'Không dùng voucher')]+[(str(x['id']),x['label']) for x in available(user,'WEB')])

    def clean(self):
        values=super().clean()
        values=clean_schedule_parts(self, values)
        from .vouchers import enabled
        duplicate = hasattr(self.data, 'getlist') and len(self.data.getlist('voucher')) > 1
        if enabled() and (self.data.get('voucher_code') or duplicate):
            raise forms.ValidationError('Chỉ chọn một voucher từ danh sách, không nhập mã thủ công.')
        if values.get('scheduled_for'):
            from datetime import timedelta
            started = self.request.session.get('menu_entered_at') if self.request else None
            try:
                started = timezone.datetime.fromisoformat(started) if started else timezone.now()
                if timezone.is_naive(started):
                    started = timezone.make_aware(started)
            except (TypeError, ValueError):
                started = timezone.now()
            values['menu_started_at'] = started
            if values['scheduled_for'] < max(timezone.now(), started + timedelta(minutes=35)):
                self.add_error(None, 'Thời gian nhận hàng không hợp lệ, vui lòng chọn lại thời gian nhận hàng.')
        from support.policies import clean_form
        return clean_form(self, values)


class PaymentScheduleForm(forms.Form):
    scheduled_date = forms.DateField(label='Ngày nhận món', required=False,
        input_formats=['%Y-%m-%d'], widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
    scheduled_hour = forms.ChoiceField(label='Giờ nhận món', required=False, choices=HOUR_CHOICES)
    scheduled_minute = forms.ChoiceField(label='Phút nhận món', required=False, choices=MINUTE_CHOICES)

    def clean(self):
        return clean_schedule_parts(self, super().clean())
