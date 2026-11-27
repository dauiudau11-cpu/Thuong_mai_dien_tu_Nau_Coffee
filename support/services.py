from django.core.exceptions import ValidationError
from django.db import transaction
from commerce.models import OrderItem
from .models import Review, SubmissionLimit
import hashlib
import time


@transaction.atomic
def allow_submission(request, scope, limit=5):
    # Hash the direct peer, never trust spoofable forwarded headers or store raw IPs.
    identity = str(request.user.pk) if request.user.is_authenticated else request.META.get('REMOTE_ADDR', '')
    key = scope + ':' + hashlib.sha256(identity.encode()).hexdigest() + ':' + str(int(time.time()) // 600)
    bucket, _ = SubmissionLimit.objects.get_or_create(key=key)
    bucket = SubmissionLimit.objects.select_for_update().get(pk=bucket.pk)
    if bucket.count >= limit:
        return False
    bucket.count += 1
    bucket.save(update_fields=['count'])
    return True


@transaction.atomic
def submit_review(user, product, data):
    item = OrderItem.objects.select_for_update().filter(pk=data['item'], order__user=user,
        order__status='COMPLETED', variant__product=product).first()
    if not item or Review.objects.filter(item=item).exists():
        raise ValidationError('Chỉ đánh giá một lần cho mỗi món trong đơn đã hoàn tất của chính bạn.')
    review = Review(item=item, user=user, product=product, rating=data['rating'], body=data['body'])
    review.full_clean()
    review.save()
    return review
