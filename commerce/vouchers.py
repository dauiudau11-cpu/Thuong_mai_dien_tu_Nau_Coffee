"""Versioned campaigns. Legacy rows are never reclassified or recounted."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, transaction
from django.utils import timezone
from catalog.permissions import has_role
from .models import Voucher, VoucherCampaign, VoucherGrant, VoucherGrantAudit, VoucherRedemption, VoucherUseV2

def enabled():
    return settings.NAU_VOUCHERS_V2_ENABLED

def table_exists(name):
    return name in connection.introspection.table_names()

def campaign_for(voucher):
    if not table_exists('commerce_vouchercampaign'):
        return None
    return VoucherCampaign.objects.filter(voucher=voucher).first()

def has_new_policy(redemption):
    return table_exists('commerce_voucherusev2') and VoucherUseV2.objects.filter(redemption=redemption).exists()

def parse_selection(value):
    if value in ('', None):
        return None
    text = str(value)
    if not text.isascii() or not text.isdecimal() or len(text) > 11 or (int(text) < 1):
        raise ValidationError('Lựa chọn voucher không hợp lệ.')
    return int(text)

def eligible_customer(user):
    """Keep legacy logins, but never let pending or privileged identities use V2."""
    if (not user or not user.is_authenticated or not user.is_active
            or user.is_staff or user.is_superuser
            or not has_role(user, 'CUSTOMER') or has_role(user, 'STAFF', 'ADMIN')):
        return False
    from catalog.customer_models import CustomerProfile
    return not CustomerProfile.objects.filter(
        user=user, origin__in=['PUBLIC', 'STAFF'], email_verified_at__isnull=True).exists()


def amount_for(voucher, subtotal):
    discount = subtotal * voucher.amount // 100 if voucher.kind == 'PERCENT' else voucher.amount
    if voucher.cap is not None:
        discount = min(discount, voucher.cap)
    return min(discount, subtotal)

def legacy_check(voucher, user, subtotal, has_sale):
    rows = voucher.redemptions.filter(is_active=True)
    if subtotal < voucher.min_subtotal or rows.count() >= voucher.max_uses or rows.filter(user=user).count() >= voucher.per_user_limit:
        raise ValidationError('Voucher không đáp ứng giá trị tối thiểu hoặc đã hết lượt.')
    if has_sale and (not voucher.allow_sale_stacking):
        raise ValidationError('Voucher không cộng dồn với giá khuyến mại.')

@transaction.atomic
def quote_selection(value, user, channel, subtotal, has_sale=False):
    pk = parse_selection(value)
    if pk is None:
        return (None, 0, None)
    if channel == 'APP':
        raise ValidationError('Đơn APP không được dùng voucher.')
    if not enabled():
        raise ValidationError('Voucher theo danh sách chưa được mở.')
    if channel not in ('WEB', 'COUNTER') or not user or (not user.is_authenticated) or (not user.is_active):
        raise ValidationError('Cần xác minh đúng tài khoản khách để dùng voucher.')
    voucher = Voucher.objects.select_for_update().filter(pk=pk, is_active=True).first()
    now = timezone.now()
    if not voucher or not voucher.starts_at <= now < voucher.ends_at:
        raise ValidationError('Voucher không tồn tại hoặc đã hết hạn.')
    campaign = VoucherCampaign.objects.select_for_update().filter(voucher=voucher).first()
    if not campaign:
        if channel != 'WEB':
            raise ValidationError('Voucher cũ chỉ theo luồng WEB hiện hành.')
        legacy_check(voucher, user, subtotal, has_sale)
        return (voucher, amount_for(voucher, subtotal), None)
    if not eligible_customer(user):
        raise ValidationError('Campaign mới chỉ dành cho tài khoản khách hàng hợp lệ.')
    if subtotal < voucher.min_subtotal or campaign.uses.count() >= voucher.max_uses:
        raise ValidationError('Chưa đạt giá trị tối thiểu hoặc campaign đã hết lượt.')
    if has_sale and (not voucher.allow_sale_stacking):
        raise ValidationError('Voucher không cộng dồn với giá khuyến mại.')
    grant = None
    if campaign.audience == 'PUBLIC':
        if campaign.uses.filter(user=user).exists():
            raise ValidationError('Tài khoản đã dùng voucher công khai này.')
    else:
        grant = VoucherGrant.objects.select_for_update().filter(campaign=campaign, user=user).first()
        if not grant or grant.used >= grant.allocated:
            raise ValidationError('Tài khoản chưa được cấp hoặc đã hết lượt voucher riêng.')
    return (voucher, amount_for(voucher, subtotal), {'campaign': campaign, 'grant': grant})

def record_use(order, user, voucher, policy):
    """Caller holds order transaction and the quote's voucher/campaign/grant locks."""
    redemption = VoucherRedemption.objects.create(order=order, user=user, voucher=voucher)
    if policy:
        campaign, grant = (policy['campaign'], policy['grant'])
        ordinal = 1
        if grant:
            grant.used += 1
            grant.save(update_fields=['used'])
            ordinal = grant.used
        VoucherUseV2.objects.create(redemption=redemption, campaign=campaign, user=user, grant=grant, ordinal=ordinal, audience=campaign.audience, snapshot={'version': 2, 'code': voucher.code, 'audience': campaign.audience, 'kind': voucher.kind, 'amount': voucher.amount, 'cap': voucher.cap, 'min_subtotal': voucher.min_subtotal, 'discount': order.discount, 'channel': order.channel})
    return redemption

def available(user, channel):
    if not enabled() or channel == 'APP' or (not user) or (not user.is_authenticated) or (not user.is_active):
        return []
    now = timezone.now()
    choices = []
    for voucher in Voucher.objects.filter(is_active=True, starts_at__lte=now, ends_at__gt=now).order_by('code'):
        campaign = campaign_for(voucher)
        if campaign:
            if not eligible_customer(user):
                continue
            if campaign.uses.count() >= voucher.max_uses:
                continue
            if campaign.audience == 'PUBLIC':
                if campaign.uses.filter(user=user).exists():
                    continue
                label = 'Công khai · 1 lần'
            else:
                grant = VoucherGrant.objects.filter(campaign=campaign, user=user).first()
                if not grant or grant.used >= grant.allocated:
                    continue
                label = f'Riêng · còn {grant.allocated - grant.used} lượt'
        else:
            if channel != 'WEB':
                continue
            rows = voucher.redemptions.filter(is_active=True)
            if rows.count() >= voucher.max_uses or rows.filter(user=user).count() >= voucher.per_user_limit:
                continue
            label = 'Chính sách cũ'
        choices.append({'id': voucher.pk, 'label': f'{voucher.code} — {label} · đơn tối thiểu {voucher.min_subtotal:,} đ'})
    return choices

@transaction.atomic
def grant_uses(actor, campaign_id, user_id, extra, reason):
    if not enabled() or not has_role(actor, 'ADMIN'):
        raise PermissionDenied
    if type(extra) is not int or not 1 <= extra <= 100000 or (not reason.strip()):
        raise ValidationError('Nhập số lượt hợp lệ và lý do cấp lượt.')
    customer = get_user_model().objects.get(pk=user_id)
    if not eligible_customer(customer):
        raise ValidationError('Chỉ cấp voucher cho tài khoản Customer hợp lệ.')
    campaign = VoucherCampaign.objects.get(pk=campaign_id)
    Voucher.objects.select_for_update().get(pk=campaign.voucher_id)
    campaign = VoucherCampaign.objects.select_for_update().get(pk=campaign_id)
    if campaign.audience != 'PRIVATE':
        raise ValidationError('Chỉ cấp lượt cho campaign riêng.')
    grant, _ = VoucherGrant.objects.select_for_update().get_or_create(campaign=campaign, user=customer)
    before = grant.allocated
    grant.allocated += extra
    grant.full_clean()
    grant.save()
    VoucherGrantAudit.objects.create(grant=grant, actor=actor, before=before, after=grant.allocated, reason=reason.strip()[:250])
    return grant

def public_campaigns(queryset):
    """Never expose private campaign codes through storefront pages, even flag OFF."""
    if table_exists('commerce_vouchercampaign'):
        return queryset.exclude(campaign_v2__audience='PRIVATE')
    return queryset
