from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def merge_guest_cart(sender, request, user, **kwargs):
    if request is not None:
        from .services import get_cart
        # Django's test client login request lacks AuthenticationMiddleware.user.
        request.user = user
        get_cart(request)
