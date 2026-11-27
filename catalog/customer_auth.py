from django.contrib.auth.backends import ModelBackend
from .customer_accounts import enabled


class CustomerModelBackend(ModelBackend):
    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        if enabled():
            from .customer_models import CustomerProfile
            # Old active users without profiles keep their existing login.
            if CustomerProfile.objects.filter(user=user, origin__in=['PUBLIC', 'STAFF'], email_verified_at__isnull=True).exists():
                return False
        return True
