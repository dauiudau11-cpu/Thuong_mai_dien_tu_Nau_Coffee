from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q


class SubmissionLimit(models.Model):
    key = models.CharField(max_length=120, unique=True)
    count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class Policy(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=150)
    body = models.TextField(max_length=10000)

    def __str__(self):
        return self.title


class Message(models.Model):
    kind = models.CharField(max_length=10, choices=[('CONTACT', 'Liên hệ'), ('FEEDBACK', 'Phản hồi')])
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    order = models.ForeignKey('commerce.Order', null=True, blank=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150)
    body = models.TextField(max_length=3000)
    status = models.CharField(max_length=10, default='NEW', choices=[('NEW', 'Mới'), ('WORKING', 'Đang xử lý'), ('RESOLVED', 'Đã xử lý')])
    admin_reply = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', '-pk']


class Review(models.Model):
    item = models.OneToOneField('commerce.OrderItem', related_name='review', on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    product = models.ForeignKey('catalog.Product', related_name='reviews', on_delete=models.PROTECT)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    body = models.TextField(max_length=2000)
    status = models.CharField(max_length=10, default='PENDING', choices=[('PENDING', 'Chờ duyệt'), ('APPROVED', 'Đã duyệt'), ('REJECTED', 'Từ chối')])
    moderated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, related_name='+', on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.CheckConstraint(condition=Q(rating__gte=1, rating__lte=5), name='review_rating_range')]

# Separate from the one-use Staff identity consent; these retain policy evidence.
from .policy_models import PolicyRevision, ConsentEvent  # noqa: E402,F401
