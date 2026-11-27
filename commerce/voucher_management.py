"""Unified voucher administration. Legacy policy and checkout services are untouched."""
import hashlib
import hmac
import json
import re
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.core import signing
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.db.models import Q, Count
from django.forms import formset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.debug import sensitive_post_parameters
from catalog.permissions import roles_required, has_role
from .models import Voucher, VoucherCampaign, VoucherGrant, VoucherGrantAudit
from . import vouchers
from .voucher_forms import GrantForm


def verified_customers():
    return get_user_model().objects.filter(is_active=True,is_staff=False,is_superuser=False,
        groups__name='CUSTOMER',customer_profile__email_verified_at__isnull=False,
        customer_profile__isnull=False).exclude(groups__name__in=['STAFF','ADMIN']).distinct()


def version(voucher, actor):
    grants = list(VoucherGrant.objects.filter(campaign__voucher=voucher).order_by('user_id').values_list('user_id','allocated')) if voucher else []
    return signing.dumps({'actor':actor.pk,'voucher':voucher.pk if voucher else None,
        'updated':voucher.updated_at.isoformat() if voucher else None,'grants':hashlib.sha256(json.dumps(grants).encode()).hexdigest()},salt='nau.voucher.admin.v1')


def verify_version(token, voucher, actor):
    try:
        data=signing.loads(token,salt='nau.voucher.admin.v1',max_age=7200)
        current=signing.loads(version(voucher,actor),salt='nau.voucher.admin.v1')
        if data != current:raise ValidationError('Voucher hoặc lượt cấp đã thay đổi. Tải lại trang trước khi lưu.')
    except signing.BadSignature:
        raise ValidationError('Phiên chỉnh sửa đã hết hạn. Tải lại trang trước khi lưu.') from None


class VoucherForm(forms.ModelForm):
    kind=forms.ChoiceField(label='Cách giảm giá',choices=[('FIXED','Số tiền cố định'),('PERCENT','Theo phần trăm')])
    audience=forms.ChoiceField(label='Phạm vi áp dụng',choices=[('PUBLIC','CÔNG KHAI (PUBLIC)'),('PRIVATE','VIP (PRIVATE)')])
    version=forms.CharField(widget=forms.HiddenInput,required=False)
    reason=forms.CharField(label='Lý do điều chỉnh lượt',max_length=220,required=False)
    class Meta:
        model=Voucher
        fields=['code','kind','amount','cap','min_subtotal','max_uses','starts_at','ends_at','is_active','allow_sale_stacking']
        labels={'code':'Tên voucher','kind':'Cách giảm giá','amount':'Giá trị giảm','cap':'Trần giảm (đ)','min_subtotal':'Đơn tối thiểu (đ)','max_uses':'Giới hạn tổng lượt','starts_at':'Bắt đầu','ends_at':'Kết thúc','is_active':'Đang mở','allow_sale_stacking':'Cộng dồn với giá khuyến mại'}
        widgets={k:forms.DateTimeInput(format='%Y-%m-%dT%H:%M:%S',attrs={'type':'datetime-local','step':'1'}) for k in ('starts_at','ends_at')}
    def __init__(self,*args,actor=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.actor=actor
        self.original_dates={k:getattr(self.instance,k) for k in ('starts_at','ends_at')} if self.instance.pk else {}
        if self.instance.pk:
            campaign=VoucherCampaign.objects.filter(voucher=self.instance).first()
            if not campaign:
                self.fields['audience'].choices=[('LEGACY','Chính sách trước đây — giữ nguyên')]
                self.fields['legacy_limit']=forms.IntegerField(label='Giới hạn mỗi tài khoản theo chính sách cũ',min_value=0,initial=self.instance.per_user_limit)
            self.fields['audience'].initial=campaign.audience if campaign else 'LEGACY'
            self.fields['audience'].disabled=True
            self.fields['audience'].help_text='Phạm vi đã lưu được giữ cố định để bảo toàn lịch sử.'
        if actor:
            self.fields['version'].initial=version(self.instance if self.instance.pk else None,actor)


    def clean_code(self):
        code=self.cleaned_data['code']
        if Voucher.objects.filter(code__iexact=code).exclude(pk=self.instance.pk).exists():raise ValidationError('Tên voucher đã được sử dụng.')
        return code

    def clean(self):
        values=super().clean()
        for key,original in self.original_dates.items():
            if values.get(key)==original.replace(microsecond=0):values[key]=original
        amount=values.get('amount')
        if amount is not None and (amount<1 or (values.get('kind')=='PERCENT' and amount>100)):
            self.add_error('amount','Mức giảm phải lớn hơn 0; phần trăm không vượt quá 100.')
        if values.get('starts_at') and values.get('ends_at') and values['ends_at']<=values['starts_at']:
            self.add_error('ends_at','Thời gian kết thúc phải sau thời gian bắt đầu.')
        return values


class AllocationForm(forms.Form):
    selected=forms.BooleanField(label='Áp dụng điều chỉnh',required=False)
    customer_id=forms.IntegerField(min_value=1,widget=forms.HiddenInput)
    allocated=forms.IntegerField(label='Tổng lượt được cấp',min_value=0,max_value=2147483647)
    expected=forms.IntegerField(min_value=0,widget=forms.HiddenInput,required=False)
    label=forms.CharField(label='Khách hàng',required=False,disabled=True)

AllocationSet=formset_factory(AllocationForm,extra=0,max_num=100,validate_max=True,absolute_max=100)


@transaction.atomic
def save_voucher(actor, form, allocation_set):
    if not has_role(actor,'ADMIN') or not vouchers.enabled():raise PermissionDenied
    new=not form.instance.pk
    locked=None if new else Voucher.objects.select_for_update().get(pk=form.instance.pk)
    if not new:
        verify_version(form.cleaned_data.get('version',''),locked,actor)
    elif form.cleaned_data.get('version'):
        verify_version(form.cleaned_data['version'],None,actor)
    campaign=VoucherCampaign.objects.select_for_update().filter(voucher=locked).first() if locked else None
    audience=campaign.audience if campaign else ('LEGACY' if locked else form.cleaned_data['audience'])
    rows=[f.cleaned_data for f in allocation_set if f.cleaned_data and f.cleaned_data.get('selected')]
    if len({r['customer_id'] for r in rows})!=len(rows):raise ValidationError('Mỗi khách hàng chỉ xuất hiện một lần trong phân bổ.')
    if audience!='PRIVATE' and rows:raise ValidationError('Chỉ voucher VIP được cấp lượt riêng.')
    if new and audience=='PRIVATE' and not rows:raise ValidationError('Chọn ít nhất một khách hàng đã xác minh và cấp lượt cho voucher VIP.')
    if campaign and form.cleaned_data['max_uses']<campaign.uses.count():raise ValidationError('Giới hạn tổng lượt không được thấp hơn số lượt đã sử dụng.')
    if rows and not form.cleaned_data.get('reason','').strip():raise ValidationError('Nhập lý do cấp hoặc điều chỉnh lượt.')
    # Lock order matches quote/record_use: voucher -> campaign -> grants (user_id order).
    grants={g.user_id:g for g in VoucherGrant.objects.select_for_update().filter(campaign=campaign).order_by('user_id')} if campaign else {}
    for row in rows:
        grant=grants.get(row['customer_id']);old=grant.allocated if grant else 0;used=grant.used if grant else 0
        if (row.get('expected') or 0)!=old:raise ValidationError('Lượt cấp đã thay đổi. Tải lại trang để tiếp tục.')
        if row['allocated']-old>100000:raise ValidationError('Mỗi lần cấp thêm tối đa 100.000 lượt cho một khách.')
        if row['allocated']<used:raise ValidationError('Không thể cấp tổng lượt thấp hơn số lượt khách đã sử dụng.')
        if not grant or row['allocated']>old:
            if not verified_customers().filter(pk=row['customer_id']).exists():raise ValidationError('Chỉ cấp lượt mới cho khách hàng đã xác minh, không phải nhân viên hoặc quản trị viên.')
        if new and row['allocated']<1:raise ValidationError('Khách được chọn cần ít nhất một lượt.')
    voucher=form.save(commit=False)
    if new:voucher.per_user_limit=1
    elif audience=='LEGACY':voucher.per_user_limit=form.cleaned_data['legacy_limit']
    voucher.full_clean();voucher.save()
    if new:campaign=VoucherCampaign.objects.create(voucher=voucher,audience=audience,created_by=actor)
    for row in sorted(rows,key=lambda r:r['customer_id']):
        grant=grants.get(row['customer_id'])
        if not grant:grant=VoucherGrant(campaign=campaign,user_id=row['customer_id'],allocated=0)
        before=grant.allocated
        if before==row['allocated']:continue
        grant.allocated=row['allocated'];grant.full_clean();grant.save()
        VoucherGrantAudit.objects.create(grant=grant,actor=actor,before=before,after=grant.allocated,reason=form.cleaned_data['reason'].strip())
    LogEntry.objects.log_actions(user_id=actor.pk,queryset=Voucher.objects.filter(pk=voucher.pk),action_flag=ADDITION if new else CHANGE,change_message='Tạo voucher' if new else 'Cập nhật voucher và phân bổ được chọn')
    return voucher


def workspace_url(request,action='list',voucher=None):
    from django.contrib import admin
    from django.urls import reverse
    model_admin=admin.site._registry[Voucher]
    native=admin.site.has_permission(request)
    if action=='add':native=native and model_admin.has_add_permission(request)
    elif action=='edit':native=native and model_admin.has_change_permission(request,voucher)
    else:native=native and model_admin.has_view_or_change_permission(request)
    if native:
        return reverse('admin:commerce_voucher_'+{'list':'changelist','add':'add','edit':'change'}[action],args=[voucher.pk] if action=='edit' else None)
    return reverse({'list':'voucher_campaigns','add':'voucher_create','edit':'voucher_edit'}[action],args=[voucher.pk] if action=='edit' else None)


def allocation_initial(voucher):
    if not voucher:return []
    rows=VoucherGrant.objects.filter(campaign__voucher=voucher).select_related('user','user__customer_profile').order_by('user_id')[:100]
    return [{'customer_id':g.user_id,'allocated':g.allocated,'expected':g.allocated,'label':g.user.get_username(),'selected':False} for g in rows]


def editor(request,voucher=None,read_only=False):
    if not has_role(request.user,'ADMIN'):raise PermissionDenied
    if not vouchers.enabled():
        from django.http import Http404
        raise Http404
    initial=allocation_initial(voucher)
    form=VoucherForm(request.POST or None,instance=voucher,actor=request.user)
    allocations=AllocationSet(request.POST or None,prefix='alloc',initial=initial)
    if read_only:
        for field in form.fields.values():field.disabled=True
        for allocation in allocations:
            for field in allocation.fields.values():field.disabled=True
    if request.method=='POST' and not read_only and form.is_valid() and allocations.is_valid():
        try:
            saved=save_voucher(request.user,form,allocations)
            from django.urls import reverse
            return redirect(workspace_url(request,'edit',saved))
        except ValidationError as error:form.add_error(None,error)
        except IntegrityError:form.add_error(None,'Tên voucher đã được sử dụng hoặc dữ liệu vừa thay đổi. Kiểm tra và gửi lại.')
    campaign=VoucherCampaign.objects.filter(voucher=voucher).first() if voucher else None
    grants=list(VoucherGrant.objects.filter(campaign=campaign).select_related('user')) if campaign else []
    for grant in grants:grant.remaining=grant.allocated-grant.used
    uses=campaign.uses.select_related('redemption__order','user').order_by('-pk') if campaign else (voucher.redemptions.select_related('order','user').order_by('-pk') if voucher else [])
    audit_rows=VoucherGrantAudit.objects.filter(grant__campaign=campaign).select_related('actor','grant__user').order_by('-pk') if campaign else []
    audit=Paginator(audit_rows,20).get_page(request.GET.get('audit_page'))
    for row in audit:row.display_reason=re.sub(r'\s+\[compat:[0-9a-f]{16}\]$','',row.reason)
    total=campaign.uses.count() if campaign else (voucher.redemptions.filter(is_active=True).count() if voucher else 0)
    return render(request,'commerce/voucher_editor.html',{'read_only':read_only,'list_url':workspace_url(request),'form':form,'allocations':allocations,'voucher':voucher,'campaign':campaign,'grants':grants,'uses':Paginator(uses,20).get_page(request.GET.get('page')),'audit':audit,'total_used':total,'remaining':max(0,voucher.max_uses-total) if voucher else 0})


@roles_required('ADMIN')
def create(request):return editor(request)

@roles_required('ADMIN')
def detail(request,pk):return editor(request,get_object_or_404(Voucher,pk=pk))

@roles_required('ADMIN')
@require_POST
@sensitive_post_parameters('q')
def customer_search(request):
    if not vouchers.enabled():
        from django.http import Http404
        raise Http404
    q=request.POST.get('q','').strip()[:100]
    customers=verified_customers().select_related('customer_profile')
    if q:
        phone=q.replace(' ','').replace('-','')
        if phone.startswith('0'):phone='+84'+phone[1:]
        customers=customers.filter(Q(username__icontains=q)|Q(customer_profile__full_name__icontains=q)|Q(customer_profile__phone__icontains=phone))
    try:
        voucher_id=forms.IntegerField(required=False,min_value=1,max_value=9223372036854775807).clean(request.POST.get('voucher_id'))
    except ValidationError:
        return JsonResponse({'error':'Voucher không hợp lệ.'},status=400)
    customers=list(customers.order_by('username')[:20])
    # Return the real baseline even after a row was cleared or lies outside the first batch.
    grants={g.user_id:g for g in VoucherGrant.objects.filter(campaign__voucher_id=voucher_id,user_id__in=[u.pk for u in customers])} if voucher_id else {}
    data=[{'id':u.pk,'label':f'{u.customer_profile.full_name} · {u.username} · {u.customer_profile.phone}',
        'has_grant':u.pk in grants,'allocated':grants[u.pk].allocated if u.pk in grants else 0,
        'used':grants[u.pk].used if u.pk in grants else 0} for u in customers]
    response=JsonResponse({'customers':data});response['Cache-Control']='no-store';return response


@transaction.atomic
def legacy_grant_compat(request,form):
    """Old POST clients remain functional; exact replays in one login never add twice."""
    data=form.cleaned_data;campaign=data['campaign']
    if not verified_customers().filter(pk=data['user'].pk).exists():raise ValidationError('Khách hàng cần xác minh tài khoản trước khi cấp thêm lượt.')
    Voucher.objects.select_for_update().get(pk=campaign.voucher_id)
    VoucherCampaign.objects.select_for_update().get(pk=campaign.pk)
    body=json.dumps([request.user.pk,getattr(request.session,'session_key',''),campaign.pk,data['user'].pk,data['extra'],data['reason']],sort_keys=True)
    marker=hmac.new(settings.SECRET_KEY.encode(),body.encode(),hashlib.sha256).hexdigest()[:16]
    suffix=' [compat:'+marker+']'
    if VoucherGrantAudit.objects.filter(grant__campaign=campaign,actor=request.user,reason__endswith=suffix).exists():return
    vouchers.grant_uses(request.user,campaign.pk,data['user'].pk,data['extra'],data['reason'].strip()[:220]+suffix)

@roles_required('ADMIN')
def index(request):
    if not vouchers.enabled():
        from django.http import Http404
        raise Http404
    error=None
    if request.method=='POST':
        if request.POST.get('action')=='grant':
            grant_form=GrantForm(request.POST)
            if grant_form.is_valid():
                try:legacy_grant_compat(request,grant_form)
                except ValidationError as e:error=' '.join(e.messages)
                else:return redirect('voucher_campaigns')
            else:error='Kiểm tra khách hàng, số lượt và lý do cấp.'
        elif request.POST.get('action')=='campaign':
            return editor(request)
        else:error='Thao tác không hợp lệ. Mở voucher để chỉnh sửa.'
    query=request.GET.get('q','').strip()[:100];audience=request.GET.get('audience','');status=request.GET.get('status','')
    if not status and request.GET.get('is_active__exact') in ('0','1'):status='active' if request.GET['is_active__exact']=='1' else 'inactive'
    rows=Voucher.objects.select_related('campaign_v2').annotate(new_used=Count('campaign_v2__uses',distinct=True),old_used=Count('redemptions',filter=Q(redemptions__is_active=True),distinct=True)).order_by('-pk')
    campaigns=VoucherCampaign.objects.select_related('voucher').order_by('-pk')
    kind=request.GET.get('kind',request.GET.get('kind__exact',''))
    if kind in ('PERCENT','FIXED'):rows=rows.filter(kind=kind);campaigns=campaigns.filter(voucher__kind=kind)
    if query:rows=rows.filter(code__icontains=query);campaigns=campaigns.filter(voucher__code__icontains=query)
    if audience in ('PUBLIC','PRIVATE'):rows=rows.filter(campaign_v2__audience=audience);campaigns=campaigns.filter(audience=audience)
    elif audience=='LEGACY':rows=rows.filter(campaign_v2__isnull=True);campaigns=campaigns.none()
    if status in ('active','inactive'):
        rows=rows.filter(is_active=status=='active');campaigns=campaigns.filter(voucher__is_active=status=='active')
    elif status=='expired':rows=rows.filter(ends_at__lte=timezone.now())
    page=Paginator(rows,20).get_page(request.GET.get('page'))
    from django.urls import reverse
    for row in page:
        campaign=getattr(row,'campaign_v2',None);row.scope=campaign.audience if campaign else 'LEGACY'
        row.used_count=row.new_used if campaign else row.old_used;row.remaining_count=max(0,row.max_uses-row.used_count)
        row.scope_label={'PUBLIC':'Công khai','PRIVATE':'VIP','LEGACY':'Chính sách cũ'}[row.scope]
        row.kind_label={'PERCENT':'Phần trăm','FIXED':'Số tiền cố định'}.get(row.kind,row.kind)
        row.state_label='Đã ngừng' if not row.is_active else ('Hết hạn' if row.ends_at<=timezone.now() else ('Sắp áp dụng' if row.starts_at>timezone.now() else 'Đang áp dụng'))
        row.used_count=row.new_used if hasattr(row,'campaign_v2') else row.old_used
        row.remaining_count=max(0,row.max_uses-row.used_count)
        row.edit_url=workspace_url(request,'edit',row)
    return render(request,'commerce/voucher_campaigns.html',{'list_url':workspace_url(request),'create_url':workspace_url(request,'add'),'voucher_page':page,'campaigns':Paginator(campaigns,20).get_page(request.GET.get('page')),'q':query,'audience':audience,'status':status,'error':error,'form':VoucherForm(actor=request.user),'grants':GrantForm(),'legacy_count':Voucher.objects.filter(campaign_v2__isnull=True).count()})
