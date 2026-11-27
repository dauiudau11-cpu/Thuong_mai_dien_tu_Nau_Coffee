"""Owner-approved release import; callers must separately attest the target DB."""
from datetime import datetime
from zoneinfo import ZoneInfo
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import transaction
from .models import Policy,PolicyRevision
from . import policies
from catalog.permissions import has_role

@transaction.atomic
def publish_release(actor,rows):
    if not policies.enabled() or not has_role(actor,'ADMIN') or not actor.has_perm('support.change_policy'):raise PermissionDenied
    if len(rows)!=11 or {r['slug'] for r in rows}!={s for s,t in policies.SECTIONS}:raise ValidationError('Release phải có đúng 11 chính sách.')
    result=[]
    for row in sorted(rows,key=lambda x:x['slug']):
        if row.get('policy_date')!='2026-11-01' or not row.get('reviewed') or not row.get('review_note'):raise ValidationError('Thiếu phê duyệt hoặc ngày chính sách đã chốt.')
        effective=datetime(2026,11,1,tzinfo=ZoneInfo('Asia/Ho_Chi_Minh'))
        policy,_=Policy.objects.get_or_create(slug=row['slug'],defaults={'title':row['title'],'body':'Nội dung được quản lý theo phiên bản chính sách.'})
        Policy.objects.select_for_update().get(pk=policy.pk)
        revision,created=PolicyRevision.objects.get_or_create(policy=policy,version=row['version'],defaults={
            'title':row['title'],'body':row['body'],'effective_at':effective,'reviewed':True,
            'review_note':row['review_note'],'created_by':actor})
        if revision.body!=row['body'] or revision.title!=row['title'] or revision.effective_at!=effective:
            raise ValidationError('Phiên bản hiện có khác release; không ghi đè.')
        if revision.status=='DRAFT':revision=policies.publish(actor,revision.pk)
        elif revision.status!='PUBLISHED':raise ValidationError('Phiên bản release đã được thay thế; không tự kích hoạt lại.')
        result.append(revision)
    return result
