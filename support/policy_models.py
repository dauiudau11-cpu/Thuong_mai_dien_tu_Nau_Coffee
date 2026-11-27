"""Versioned policy evidence; no migration/backfill of legacy policy bodies or users."""
import hashlib
import json
from datetime import timezone as utc
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class PolicyRevision(models.Model):
    # effective_at is the declared policy date; publication/consent clocks are never backdated.
    policy = models.ForeignKey('support.Policy', on_delete=models.PROTECT, related_name='revisions')
    version = models.CharField('Phiên bản', max_length=40)
    title = models.CharField('Tiêu đề', max_length=150)
    body = models.TextField('Nội dung (văn bản, không thực thi HTML)', max_length=30000)
    effective_at = models.DateTimeField('Ngày hiệu lực', null=True, blank=True)
    status = models.CharField(max_length=12, choices=[('DRAFT','Bản nháp'),('PUBLISHED','Đã công bố'),('ARCHIVED','Phiên bản trước')], default='DRAFT')
    reviewed = models.BooleanField('Đã đối chiếu nghiệp vụ và được duyệt nội dung', default=False)
    review_note = models.CharField('Ghi chú duyệt/căn cứ kiểm tra', max_length=1000, blank=True)
    substantial_change = models.BooleanField('Thay đổi đáng kể: cần thông báo/xem lại chấp thuận', default=True)
    content_hash = models.CharField(max_length=64, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, editable=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['policy','version'], name='policy_version_unique'),
            models.UniqueConstraint(fields=['policy'], condition=Q(status='PUBLISHED'), name='policy_one_published')]
        ordering = ['-pk']
        verbose_name = 'Phiên bản chính sách'
        verbose_name_plural = 'Phiên bản chính sách'

    def calculate_hash(self):
        value = {'policy_id':self.policy_id,'version':self.version,'title':self.title,'body':self.body,
            'effective_at':self.effective_at.astimezone(utc.utc).isoformat() if self.effective_at else None,
            'substantial_change':self.substantial_change}
        return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    def save(self,*args,**kwargs):
        if self.pk:
            original=type(self).objects.get(pk=self.pk)
            if original.published_at and any(getattr(self,k)!=getattr(original,k) for k in ['policy_id','version','title','body','effective_at','substantial_change','reviewed','review_note','created_by_id','published_at','content_hash']):
                raise ValidationError('Phiên bản đã công bố không được sửa. Hãy tạo bản nháp mới.')
        self.content_hash=self.calculate_hash()
        self.full_clean();super().save(*args,**kwargs)

    def delete(self,*args,**kwargs):
        raise ValidationError('Giữ phiên bản để đối chiếu lịch sử; không xóa.')

    def __str__(self):return f'{self.title} — {self.version}'


class ConsentEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name='policy_events')
    revision = models.ForeignKey(PolicyRevision,on_delete=models.PROTECT,related_name='consents')
    purpose = models.CharField(max_length=24,choices=[('TERMS','Điều khoản tài khoản'),('ORDER_TERMS','Điều kiện giao dịch'),('PRIVACY_NOTICE','Thông báo quyền riêng tư'),('MARKETING','Email ưu đãi'),('ANALYTICS','Thống kê tùy chọn')])
    state = models.CharField(max_length=12,choices=[('ACCEPTED','Chấp thuận'),('DECLINED','Không chọn'),('WITHDRAWN','Rút lại'),('PRESENTED','Đã cung cấp thông báo')])
    source = models.CharField(max_length=12,choices=[('register','Đăng ký'),('checkout','Checkout'),('account','Tài khoản')])
    operation_id = models.UUIDField()
    content_hash = models.CharField(max_length=64)
    method = models.CharField(max_length=150)
    order = models.ForeignKey('commerce.Order',null=True,blank=True,on_delete=models.PROTECT,related_name='policy_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering=['-pk']
        constraints=[models.UniqueConstraint(fields=['user','operation_id','purpose','revision'],name='consent_operation_unique')]
        verbose_name='Lịch sử chấp thuận'
        verbose_name_plural='Lịch sử chấp thuận'

    def save(self,*args,**kwargs):
        if self.pk:raise ValidationError('Lịch sử chỉ được ghi nối tiếp.')
        if self.content_hash!=self.revision.content_hash:raise ValidationError('Hash chính sách không khớp.')
        self.full_clean();super().save(*args,**kwargs)

    def delete(self,*args,**kwargs):raise ValidationError('Không xóa lịch sử chấp thuận.')
