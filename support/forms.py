from django import forms
from .models import Message


class MessageForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    order_code = forms.UUIDField(label='Mã đơn của bạn (không bắt buộc)', required=False)

    class Meta:
        model = Message
        fields = ['name', 'email', 'subject', 'body']
        labels = {'name': 'Họ và tên', 'email': 'Email của bạn',
                  'subject': 'Chủ đề cần hỗ trợ', 'body': 'Lời nhắn của bạn'}
        widgets = {'body': forms.Textarea(attrs={'rows': 5})}


class ReviewForm(forms.Form):
    item = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    rating = forms.TypedChoiceField(label='Điểm đánh giá', coerce=int, choices=[(n, f'{n}/5') for n in range(5, 0, -1)])
    body = forms.CharField(label='Cảm nhận của bạn', min_length=5, max_length=2000, widget=forms.Textarea(attrs={'rows': 4}))
