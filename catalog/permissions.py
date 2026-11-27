from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def has_role(user, *roles):
    return user.is_authenticated and user.is_active and (
        user.is_superuser or user.groups.filter(name__in=roles).exists())


def effective_role(user):
    """Classify an authenticated account for login/navigation, with one precedence."""
    if not getattr(user, 'is_authenticated', False) or not user.is_active:
        return None
    if user.is_superuser or user.groups.filter(name='ADMIN').exists():
        return 'ADMIN'
    if user.groups.filter(name='STAFF').exists():
        return 'STAFF'
    if user.groups.filter(name='CUSTOMER').exists():
        return 'CUSTOMER'
    return None


def internal_home(user):
    return '/dashboard/' if effective_role(user) == 'ADMIN' else '/dashboard/kitchen/'


def is_internal_user(user):
    return effective_role(user) in ('ADMIN', 'STAFF')


def is_customer_user(user):
    return effective_role(user) == 'CUSTOMER'


def customer_required(view):
    @login_required(login_url='login')
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if not is_customer_user(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return guarded


def public_customer_only(view):
    """Public/guest commerce remains visible, but internal sessions cannot transact."""
    @wraps(view)
    def guarded(request, *args, **kwargs):
        if is_internal_user(request.user):
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return guarded


def roles_required(*roles):
    def decorate(view):
        @login_required(login_url='internal_login')
        @wraps(view)
        def guarded(request, *args, **kwargs):
            if not has_role(request.user, *roles):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return guarded
    return decorate
