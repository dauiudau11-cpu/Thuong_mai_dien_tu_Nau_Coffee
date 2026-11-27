"""One policy workspace inside the accepted Admin shell; no duplicate editor."""
from django import forms
from django.contrib import admin,messages
from django.contrib.admin.models import LogEntry,CHANGE
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404,redirect,render
from django.urls import path
from django.http import Http404
from catalog.permissions import has_role
from .models import Policy,PolicyRevision,ConsentEvent
from . import policies

class PolicyBodyWidget(forms.Textarea):
    def __init__(self,attrs=None):
        defaults={'rows':18,'class':'policy-rich-source','data-policy-rich-editor':'true','aria-describedby':'policy-editor-help'}
        if attrs:defaults.update(attrs)
        super().__init__(defaults)

class RevisionForm(forms.ModelForm):
    class Meta:
        model=PolicyRevision
        fields=['version','title','body','effective_at','reviewed','review_note','substantial_change']
        labels={'effective_at':'Ngày chính sách (không phải thời điểm công bố)'},
        widgets={'body':PolicyBodyWidget(),'effective_at':forms.DateTimeInput(format='%Y-%m-%dT%H:%M:%S',attrs={'type':'datetime-local','step':'1'})}

class NewPolicyForm(forms.ModelForm):
    class Meta:
        model=Policy
        fields=['slug','title','body']
        labels={'slug':'Đường dẫn định danh','title':'Tiêu đề','body':'Nội dung khởi tạo (chưa công bố)'}
        widgets={'body':PolicyBodyWidget()}

class PolicyAdmin(admin.ModelAdmin):
    list_display=['title','slug']
    search_fields=['title','slug']
    def get_list_display(self,request):
        return ['title','slug','publication'] if policies.enabled() else super().get_list_display(request)
    @admin.display(description='Trạng thái / phiên bản')
    def publication(self,obj):
        current=obj.revisions.filter(status='PUBLISHED').first()
        return ('Đã công bố · '+current.version) if current else 'Bản nháp / chưa công bố'
    def get_urls(self):
        return [path('<int:pk>/versions/',self.admin_site.admin_view(self.workspace),name='support_policy_versions')]+super().get_urls()
    def change_view(self,request,object_id,form_url='',extra_context=None):
        if policies.enabled():return self.workspace(request,object_id)
        return super().change_view(request,object_id,form_url,extra_context)
    def has_delete_permission(self,request,obj=None):
        return not policies.enabled() and super().has_delete_permission(request,obj)
    def has_add_permission(self,request):
        return (not policies.enabled() or has_role(request.user,'ADMIN')) and super().has_add_permission(request)
    def add_view(self,request,form_url='',extra_context=None):
        if not policies.enabled():return super().add_view(request,form_url,extra_context)
        if not self.has_add_permission(request):raise PermissionDenied
        form=NewPolicyForm(request.POST if request.method=='POST' else None)
        if request.method=='POST' and form.is_valid():
            obj=form.save();return redirect('admin:support_policy_versions',pk=obj.pk)
        return render(request,'admin/policy_workspace.html',{'form':form,'title':'Tạo nội dung chính sách','new_policy':True})
    def workspace(self,request,pk):
        if not policies.enabled() or not has_role(request.user,'ADMIN') or not self.has_view_or_change_permission(request):raise PermissionDenied
        obj=self.get_object(request,pk)
        if obj is None:raise Http404
        editable=self.has_change_permission(request,obj)
        editing=None
        draft_id=request.POST.get('draft_id') if request.method=='POST' else request.GET.get('draft')
        if draft_id:
            try:draft_id=forms.IntegerField(min_value=1,max_value=9223372036854775807).clean(draft_id)
            except ValidationError:raise Http404 from None
            editing=get_object_or_404(PolicyRevision,pk=draft_id,policy=obj,status='DRAFT',published_at__isnull=True)
        form=RevisionForm(request.POST if request.method=='POST' and request.POST.get('action') in ('draft','preview') else None,instance=editing)
        preview=None
        if request.method=='POST':
            if not editable:raise PermissionDenied
            try:
                if request.POST.get('action')=='publish':
                    revision_id=forms.IntegerField(min_value=1,max_value=9223372036854775807).clean(request.POST.get('revision'))
                    revision=get_object_or_404(PolicyRevision,pk=revision_id,policy=obj)
                    policies.publish(request.user,revision.pk)
                    messages.success(request,'Đã công bố phiên bản. Phiên bản trước được giữ lại.');return redirect(request.path)
                if form.is_valid():
                    preview=form.cleaned_data
                    if request.POST.get('action')=='draft':
                        revision=form.save(commit=False);revision.policy=obj;revision.created_by=revision.created_by if revision.pk else request.user;revision.status='DRAFT';revision.save()
                        LogEntry.objects.log_actions(user_id=request.user.pk,queryset=Policy.objects.filter(pk=obj.pk),action_flag=CHANGE,change_message='Lưu bản nháp chính sách '+revision.version)
                        messages.success(request,'Đã lưu bản nháp, chưa công bố.');return redirect(request.path)
            except ValidationError as error:form.add_error(None,error)
        return render(request,'admin/policy_workspace.html',{'policy':obj,'editing':editing,'form':form,'preview':preview,'editable':editable,
            'editing':editing,'revisions':obj.revisions.all(),'title':obj.title,'can_audit':request.user.has_perm('support.view_consentevent')})


class ConsentAdmin(admin.ModelAdmin):
    list_display=['user','purpose','state','source','revision','created_at']
    list_filter=['purpose','state','source']
    search_fields=['user__username']
    readonly_fields=[f.name for f in ConsentEvent._meta.fields]
    def has_module_permission(self,request):return False  # Linked once from policy workspace.
    def has_view_permission(self,request,obj=None):return policies.enabled() and has_role(request.user,'ADMIN') and request.user.has_perm('support.view_consentevent')
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
