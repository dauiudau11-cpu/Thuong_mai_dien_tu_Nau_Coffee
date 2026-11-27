from django import forms
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render,redirect
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.views.decorators.cache import never_cache
from . import policies
from .models import ConsentEvent


def center(request):
    if policies.enabled():
        current=policies.active()
        sections=[{'slug':slug,'title':title,'revision':current.get(slug)} for slug,title in policies.SECTIONS]
    else:
        from .views import POLICIES
        sections=[{'slug':slug,'title':title} for slug,(title,body) in POLICIES.items()]
    return render(request,'support/policy_center.html',{'sections':sections,'publication_ready':policies.enabled()})


class PreferencesForm(forms.Form):
    policy_token=forms.CharField(widget=forms.HiddenInput,max_length=8000)
    marketing=policies.ExplicitCheckbox(required=False,label='Nhận thông tin ưu đãi qua email')
    analytics=policies.ExplicitCheckbox(required=False,label='Cho phép thống kê truy cập')


@never_cache
@login_required
def preferences(request):
    if not policies.enabled():raise Http404
    initial={'marketing':policies.preference(request.user,'MARKETING'),'analytics':policies.preference(request.user,'ANALYTICS')}
    unavailable=''
    try:initial['policy_token']=policies.issue_token(request,'account')
    except ValidationError as error:unavailable=' '.join(error.messages)
    form=PreferencesForm(request.POST if request.method=='POST' else None,initial=initial)
    if request.method=='POST' and form.is_valid():
        try:policies.update_preferences(request,form.cleaned_data['policy_token'],form.cleaned_data['marketing'],form.cleaned_data['analytics'])
        except ValidationError as error:form.add_error(None,error)
        else:return redirect('policy_preferences')
    return render(request,'support/preferences.html',{'form':form,'unavailable':unavailable,
        'history':Paginator(ConsentEvent.objects.filter(user=request.user,
            purpose__in=('MARKETING','ANALYTICS')).select_related('revision','revision__policy'),20).get_page(request.GET.get('page'))})
