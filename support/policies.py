"""Policy publication and evidence, feature-gated until preview cutover is approved."""
import secrets
import uuid
from django.conf import settings
from django import forms
from django.core import signing
from django.core.exceptions import ValidationError,PermissionDenied
from django.db import transaction
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from catalog.permissions import has_role
from .models import Policy,PolicyRevision,ConsentEvent

SECTIONS=[('ordering','Đặt hàng và nhận món'),('shipping','Vận chuyển và giao nhận'),
 ('cancellation','Hủy và thay đổi đơn'),('returns','Đổi trả, hoàn tiền, chất lượng'),
 ('payment','Thanh toán'),('privacy','Bảo mật và quyền riêng tư'),('terms','Khuyến mãi và điều khoản sử dụng'),
 ('contact','Liên hệ và hỗ trợ'),('accounts','Tài khoản khách hàng'),
 ('reviews','Đánh giá, góp ý và khiếu nại'),('cookies','Cookie và dữ liệu truy cập')]
REQUIRED={'register':['terms','privacy'], 'checkout':['ordering','shipping','cancellation','returns','payment','terms'], 'account':['privacy','cookies']}
SALT='nau.policy.form.v1'


def enabled():return bool(getattr(settings,'NAU_POLICY_CONSENT_ENABLED',False))

def active():
    return {r.policy.slug:r for r in PolicyRevision.objects.select_related('policy').filter(status='PUBLISHED',effective_at__lte=timezone.now())}


def manifest(source):
    current=active()
    if any(k not in current for k in REQUIRED[source]):
        raise ValidationError('Chính sách cần thiết chưa được công bố đầy đủ. Vui lòng quay lại sau hoặc liên hệ Nâu.')
    return {k:{'id':current[k].pk,'hash':current[k].content_hash,'version':current[k].version} for k in REQUIRED[source]}


def issue_token(request,source):
    if request is None:raise ValidationError('Cần phiên trình duyệt để xác nhận chính sách.')
    nonce=request.session.setdefault('policy_form_nonce',secrets.token_hex(24))
    return signing.dumps({'nonce':nonce,'user':request.user.pk if request.user.is_authenticated else None,
        'source':source,'operation':str(uuid.uuid4()),'policies':manifest(source)},salt=SALT,compress=True)


def verify_token(request,token,source):
    if hasattr(request.POST,'getlist') and any(len(request.POST.getlist(k))>1 for k in ['policy_token','accept_terms','accept_order_terms','marketing','analytics']):
        raise ValidationError('Tham số xác nhận bị lặp. Vui lòng tải lại trang.')
    try:data=signing.loads(token,salt=SALT,max_age=3600)
    except signing.BadSignature:raise ValidationError('Phiên xác nhận không hợp lệ hoặc đã hết hạn. Vui lòng tải lại trang.') from None
    if not isinstance(data,dict):raise ValidationError('Phiên xác nhận không hợp lệ.')
    if not isinstance(data,dict):raise ValidationError('Phiên xác nhận không hợp lệ.')
    if (data.get('nonce')!=request.session.get('policy_form_nonce') or not data.get('nonce')
        or data.get('source')!=source or data.get('user')!=(request.user.pk if request.user.is_authenticated else None)
        or data.get('policies')!=manifest(source)):
        raise ValidationError('Phiên bản chính sách hoặc phiên đăng nhập đã thay đổi. Vui lòng tải lại trang.')
    try:uuid.UUID(data['operation'])
    except (ValueError,TypeError,KeyError):raise ValidationError('Phiên xác nhận không hợp lệ.') from None
    return data


class RawCheckboxInput(forms.CheckboxInput):
    def value_from_datadict(self,data,files,name):return data.get(name,False)


class ExplicitCheckbox(forms.BooleanField):
    widget=RawCheckboxInput
    def to_python(self,value):
        if value in (None,'',False,'false','0'):return False
        if value in (True,'on','true','1'):return True
        raise ValidationError('Lựa chọn xác nhận không hợp lệ.')


def add_fields(form,request,source):
    if not enabled():return
    form.policy_request=request;form.policy_source=source;form.policy_unavailable=''
    try:token=issue_token(request,source)
    except ValidationError as error:token='';form.policy_unavailable=' '.join(error.messages)
    form.fields['policy_token']=forms.CharField(widget=forms.HiddenInput,initial=token,max_length=8000)
    if source=='register':
        form.fields['accept_terms']=ExplicitCheckbox(label=format_html('Tôi đã đọc và đồng ý với <a href="{}" target="_blank" rel="noopener">Điều khoản sử dụng</a> của Nâu Coffee.',reverse('policy',args=['terms'])))
        form.fields['marketing']=ExplicitCheckbox(required=False,label='Tôi đồng ý nhận email thông tin chương trình khuyến mãi và ưu đãi từ Nâu Coffee.')
    elif source=='checkout':
        form.fields['accept_order_terms']=ExplicitCheckbox(label=format_html('Tôi đã đọc và đồng ý với <a href="{}" target="_blank" rel="noopener">Điều kiện đặt hàng, nhận món</a>, <a href="{}" target="_blank" rel="noopener">hủy đơn</a> và <a href="{}" target="_blank" rel="noopener">hoàn tiền</a> của Nâu Coffee.',reverse('policy',args=['ordering']),reverse('policy',args=['cancellation']),reverse('policy',args=['returns'])))


def clean_form(form,values):
    if enabled():
        values['_policy_proof']=verify_token(form.policy_request,values.get('policy_token',''),form.policy_source)
    return values


def _lock_revisions(proof,source):
    # Publishers and evidence writers use the same policy row locks, in stable order.
    ids=[x['id'] for x in proof['policies'].values()]
    policy_ids=PolicyRevision.objects.filter(pk__in=ids).values_list('policy_id',flat=True)
    list(Policy.objects.select_for_update().filter(pk__in=policy_ids).order_by('pk'))
    if proof['policies']!=manifest(source):raise ValidationError('Chính sách vừa thay đổi. Vui lòng xác nhận lại.')
    return {r.policy.slug:r for r in PolicyRevision.objects.select_related('policy').filter(pk__in=ids)}


def append_event(user,revision,purpose,state,source,operation,order=None):
    values=dict(state=state,source=source,content_hash=revision.content_hash,method='explicit_checkbox_post' if state!='PRESENTED' else 'notice_displayed_with_form',order=order)
    event,created=ConsentEvent.objects.get_or_create(user=user,revision=revision,purpose=purpose,operation_id=operation,defaults=values)
    if not created and any(getattr(event,k)!=v for k,v in values.items()):raise ValidationError('Yêu cầu xác nhận đã được sử dụng với lựa chọn khác.')
    return event


@transaction.atomic
def register_customer(request,values):
    proof=verify_token(request,values.get('policy_token',''),'register')
    if not values.get('accept_terms'):raise ValidationError('Vui lòng xác nhận Điều khoản sử dụng.')
    revisions=_lock_revisions(proof,'register')
    from catalog.customer_accounts import create_customer
    profile=create_customer(values)
    append_event(profile.user,revisions['terms'],'TERMS','ACCEPTED','register',proof['operation'])
    append_event(profile.user,revisions['privacy'],'PRIVACY_NOTICE','PRESENTED','register',proof['operation'])
    append_event(profile.user,revisions['privacy'],'MARKETING','ACCEPTED' if values.get('marketing') else 'DECLINED','register',proof['operation'])
    return profile


@transaction.atomic
def place_order(request,cart,values):
    proof=verify_token(request,values.get('policy_token',''),'checkout')
    if not values.get('accept_order_terms'):raise ValidationError('Vui lòng xác nhận điều kiện đặt hàng.')
    revisions=_lock_revisions(proof,'checkout')
    from commerce.services import place_order as existing_place_order
    from commerce.models import Order
    existed=Order.objects.filter(user=request.user,idempotency_key=values['idempotency_key']).exists()
    order=existing_place_order(request.user,cart,values)
    # An idempotent retry cannot manufacture new consent for an already-created order.
    if not existed and not order.policy_events.exists():
        for revision in revisions.values():append_event(request.user,revision,'ORDER_TERMS','ACCEPTED','checkout',proof['operation'],order)
    return order


def preference(user,purpose):
    if not user.is_authenticated:return False
    event=ConsentEvent.objects.filter(user=user,purpose=purpose).select_related('revision').order_by('-pk').first()
    return bool(event and event.state=='ACCEPTED' and event.revision.status=='PUBLISHED'
        and event.revision.effective_at<=timezone.now() and event.content_hash==event.revision.content_hash)


@transaction.atomic
def update_preferences(request,token,marketing,analytics):
    from django.contrib.auth import get_user_model
    proof=verify_token(request,token,'account');revisions=_lock_revisions(proof,'account')
    get_user_model().objects.select_for_update().get(pk=request.user.pk)
    for purpose,chosen,slug in [('MARKETING',marketing,'privacy'),('ANALYTICS',analytics,'cookies')]:
        previous=ConsentEvent.objects.filter(user=request.user,purpose=purpose).order_by('-pk').first()
        state='ACCEPTED' if chosen else ('WITHDRAWN' if previous and previous.state in ('ACCEPTED','WITHDRAWN') else 'DECLINED')
        append_event(request.user,revisions[slug],purpose,state,'account',proof['operation'])


@transaction.atomic
def publish(actor,revision_id):
    if not enabled() or not has_role(actor,'ADMIN') or not actor.has_perm('support.change_policy'):raise PermissionDenied
    revision=PolicyRevision.objects.get(pk=revision_id)
    Policy.objects.select_for_update().get(pk=revision.policy_id)
    revision=PolicyRevision.objects.select_for_update().get(pk=revision_id)
    if revision.status!='DRAFT' or revision.published_at:raise ValidationError('Chỉ công bố bản nháp chưa xuất bản.')
    if not revision.reviewed or not revision.review_note.strip() or not revision.effective_at or revision.effective_at>timezone.now():
        raise ValidationError('Cần duyệt nội dung, ghi căn cứ và ngày hiệu lực không ở tương lai trước khi công bố.')
    PolicyRevision.objects.filter(policy=revision.policy,status='PUBLISHED').update(status='ARCHIVED')
    revision.status='PUBLISHED';revision.published_at=timezone.now();revision.save()
    from django.contrib.admin.models import LogEntry,CHANGE
    LogEntry.objects.log_actions(user_id=actor.pk,queryset=Policy.objects.filter(pk=revision.policy_id),action_flag=CHANGE,change_message=f'Công bố chính sách {revision.version}; hash {revision.content_hash}')
    return revision
