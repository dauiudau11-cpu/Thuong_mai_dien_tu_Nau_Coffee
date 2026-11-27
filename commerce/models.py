import uuid
from datetime import time
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower
from catalog.models import ProductVariant


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Cart(Timestamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    session_key = models.UUIDField(null=True, blank=True, unique=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=(Q(user__isnull=False, session_key__isnull=True)
            | Q(user__isnull=True, session_key__isnull=False)), name='cart_owner_xor')]


class CartItem(Timestamped):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(99)])
    options = models.ManyToManyField('catalog.ProductOption', blank=True)
    config_key = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['cart', 'variant', 'config_key'], name='unique_cart_configuration'),
            models.CheckConstraint(condition=Q(quantity__gte=1, quantity__lte=99), name='cart_quantity_range')]


class Voucher(Timestamped):
    code = models.CharField(max_length=30)
    kind = models.CharField(max_length=10, choices=[('PERCENT', 'Phần trăm'), ('FIXED', 'Số tiền')])
    amount = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    cap = models.PositiveBigIntegerField(null=True, blank=True)
    min_subtotal = models.PositiveBigIntegerField(default=0)
    max_uses = models.PositiveIntegerField(default=100)
    per_user_limit = models.PositiveIntegerField(default=1)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    allow_sale_stacking = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(Lower('code'), name='voucher_code_case_unique'),
            models.CheckConstraint(condition=Q(ends_at__gt=F('starts_at')), name='voucher_dates'),
            models.CheckConstraint(condition=Q(amount__gte=1) & (Q(kind='FIXED')
                | Q(kind='PERCENT', amount__lte=100)), name='voucher_amount'),
            models.CheckConstraint(condition=Q(max_uses__gte=1, per_user_limit__gte=1), name='voucher_limits')]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class Order(Timestamped):
    class Status(models.TextChoices):
        PENDING_PAYMENT = 'PENDING_PAYMENT', 'Chờ thanh toán mô phỏng'
        PENDING_CONFIRMATION = 'PENDING_CONFIRMATION', 'Chờ nhân viên xác nhận'
        CONFIRMED = 'CONFIRMED', 'Đã xác nhận'
        PREPARING = 'PREPARING', 'Đang pha chế'
        READY = 'READY', 'Đã sẵn sàng'
        PICKUP_WAITING = 'PICKUP_WAITING', 'Chờ khách nhận'
        DELIVERING = 'DELIVERING', 'Đang giao mô phỏng'
        COMPLETED = 'COMPLETED', 'Hoàn tất'
        CANCELLED = 'CANCELLED', 'Đã hủy'
        DELIVERY_FAILED = 'DELIVERY_FAILED', 'Giao thất bại'

    public_code = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    placed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='placed_orders', on_delete=models.PROTECT)
    channel = models.CharField(max_length=10, choices=[('WEB', 'Website'), ('COUNTER', 'Quầy'), ('APP', 'App demo')], default='WEB')
    fulfillment = models.CharField(max_length=10, choices=[('PICKUP', 'Nhận tại quán'), ('DELIVERY', 'Giao hàng')])
    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    delivery_verified = models.BooleanField(default=False)
    delivery_distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bill_issued_at = models.DateTimeField(null=True, blank=True)
    delivery_deadline_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    external_reference = models.CharField(max_length=100, blank=True)
    subtotal = models.PositiveBigIntegerField()
    discount = models.PositiveBigIntegerField(default=0)
    shipping = models.PositiveBigIntegerField(default=0)
    total = models.PositiveBigIntegerField()
    status = models.CharField(max_length=30, choices=Status.choices)
    idempotency_key = models.UUIDField()

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'idempotency_key'], name='unique_user_order_request'),
            models.UniqueConstraint(fields=['placed_by', 'idempotency_key'], condition=~Q(channel='WEB'), name='unique_manual_order_request'),
            models.UniqueConstraint(fields=['channel', 'external_reference'], condition=~Q(external_reference=''), name='unique_external_order_reference'),
            models.CheckConstraint(condition=Q(discount__lte=F('subtotal')), name='discount_within_subtotal'),
            models.CheckConstraint(condition=Q(total=F('subtotal') - F('discount') + F('shipping')), name='order_total_consistent'),
            models.CheckConstraint(condition=~Q(channel='WEB') | Q(user__isnull=False), name='web_order_requires_user')]

    def __str__(self):
        return str(self.public_code)

    @property
    def delivery_is_late(self):
        if not self.delivery_deadline_at or self.status in ('CANCELLED', 'DELIVERY_FAILED'):
            return False
        from django.utils import timezone
        at = self.delivered_at if self.delivered_at else timezone.now()
        return at > self.delivery_deadline_at


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.PROTECT)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    product_name = models.CharField(max_length=150)
    sku = models.CharField(max_length=30)
    options_snapshot = models.JSONField(default=list)
    # None identifies legacy orders: do not invent their historical recipe.
    recipe_snapshot = models.JSONField(null=True, blank=True, default=None)
    unit_price = models.PositiveBigIntegerField()
    quantity = models.PositiveSmallIntegerField()
    line_total = models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gte=1, quantity__lte=99), name='order_item_quantity'),
            models.CheckConstraint(condition=Q(line_total=F('unit_price') * F('quantity')), name='order_line_consistent')]


class Payment(Timestamped):
    class Method(models.TextChoices):
        COD = 'COD', 'COD mô phỏng'
        PAY_AT_PICKUP = 'PAY_AT_PICKUP', 'Thanh toán khi nhận (demo)'
        MOCK_ONLINE = 'MOCK_ONLINE', 'Thanh toán online mô phỏng'
        EXTERNAL_DEMO = 'EXTERNAL_DEMO', 'Đối soát bên ngoài mô phỏng'
        BANK_TRANSFER_DEMO = 'BANK_TRANSFER_DEMO', 'Chuyển khoản mô phỏng'

    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Chưa ghi nhận thu'
        PENDING = 'PENDING', 'Chờ mô phỏng'
        PAID = 'PAID', 'Đã ghi nhận (demo)'
        FAILED = 'FAILED', 'Mô phỏng thất bại'
        REFUND_PENDING = 'REFUND_PENDING', 'Chờ hoàn mô phỏng'
        REFUNDED = 'REFUNDED', 'Đã hoàn mô phỏng'

    order = models.OneToOneField(Order, related_name='payment', on_delete=models.PROTECT)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    amount = models.PositiveBigIntegerField()
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)


class PaymentEvent(models.Model):
    payment = models.ForeignKey(Payment, related_name='events', on_delete=models.PROTECT)
    event_key = models.CharField(max_length=50)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['payment', 'event_key'], name='unique_payment_event')]


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, related_name='history', on_delete=models.PROTECT)
    from_state = models.CharField(max_length=30, blank=True)
    to_state = models.CharField(max_length=30)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    reason = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class VoucherRedemption(models.Model):
    voucher = models.ForeignKey(Voucher, related_name='redemptions', on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    order = models.OneToOneField(Order, related_name='redemption', on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class StoreSettings(models.Model):
    name = models.CharField(max_length=50, unique=True, default='DEMO')
    delivery_fee = models.PositiveBigIntegerField(default=15000)
    free_delivery_min = models.PositiveBigIntegerField(default=200000)
    opens_at = models.TimeField(default=time(7))
    closes_at = models.TimeField(default=time(22))
    lead_minutes = models.PositiveSmallIntegerField(default=15, validators=[MinValueValidator(1)])
    preorder_days = models.PositiveSmallIntegerField(default=7, validators=[MinValueValidator(1)])
    slot_capacity = models.PositiveSmallIntegerField(default=10, validators=[MinValueValidator(1)])
    loyalty_vnd_per_point = models.PositiveIntegerField(default=10000, validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(closes_at__gt=F('opens_at'), lead_minutes__gte=1,
            preorder_days__gte=1, slot_capacity__gte=1, loyalty_vnd_per_point__gte=1), name='valid_store_operations')]


class Ingredient(models.Model):
    sku = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=10, choices=[('g', 'g'), ('ml', 'ml'), ('piece', 'cái')])
    low_stock_threshold = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(low_stock_threshold__gte=0), name='stock_threshold_nonnegative')]

    def __str__(self):
        return f'{self.name} ({self.unit})'


class RecipeLine(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='recipe', on_delete=models.PROTECT)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))])

    class Meta:
        constraints = [models.UniqueConstraint(fields=['variant', 'ingredient'], name='unique_recipe_ingredient'),
            models.CheckConstraint(condition=Q(quantity__gt=0), name='recipe_quantity_positive')]


class OptionRecipeLine(models.Model):
    option = models.ForeignKey('catalog.ProductOption', related_name='recipe', on_delete=models.PROTECT)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['option', 'ingredient'], name='unique_option_ingredient'),
            models.CheckConstraint(condition=Q(quantity__gt=0), name='option_recipe_positive')]


class StockMovement(models.Model):
    ingredient = models.ForeignKey(Ingredient, related_name='movements', on_delete=models.PROTECT)
    delta = models.DecimalField(max_digits=14, decimal_places=3)
    reason = models.CharField(max_length=12, choices=[('PURCHASE', 'Nhập kho'), ('CONSUME', 'Pha chế'), ('ADJUST', 'Điều chỉnh'), ('WASTE', 'Hao hụt')])
    note = models.CharField(max_length=300)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT)
    idempotency_key = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.CheckConstraint(condition=~Q(delta=0), name='stock_movement_nonzero')]


class LoyaltyLedger(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='loyalty_entries', on_delete=models.PROTECT)
    order = models.ForeignKey(Order, on_delete=models.PROTECT)
    delta = models.IntegerField()
    event = models.CharField(max_length=10, choices=[('EARN', 'Tích điểm'), ('REVERSE', 'Hoàn điểm')])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [models.UniqueConstraint(fields=['order', 'event'], name='unique_order_loyalty_event')]


class VoucherCampaign(models.Model):
    voucher = models.OneToOneField(Voucher, on_delete=models.PROTECT, related_name='campaign_v2')
    audience = models.CharField(max_length=10, choices=[('PUBLIC','Công khai — một lần'),('PRIVATE','Riêng theo tài khoản')])
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(audience__in=['PUBLIC','PRIVATE']), name='voucher_v2_audience')]


class VoucherGrant(models.Model):
    campaign = models.ForeignKey(VoucherCampaign, on_delete=models.PROTECT, related_name='grants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    allocated = models.PositiveIntegerField(default=0)
    used = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['campaign','user'],name='voucher_grant_user_unique'),
                       models.CheckConstraint(condition=Q(used__lte=F('allocated')),name='voucher_grant_used_limit')]


class VoucherGrantAudit(models.Model):
    grant = models.ForeignKey(VoucherGrant,on_delete=models.PROTECT,related_name='audit')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    before = models.PositiveIntegerField()
    after = models.PositiveIntegerField()
    reason = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)


class VoucherUseV2(models.Model):
    redemption = models.OneToOneField(VoucherRedemption,on_delete=models.PROTECT,related_name='policy_v2')
    campaign = models.ForeignKey(VoucherCampaign,on_delete=models.PROTECT,related_name='uses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT)
    audience = models.CharField(max_length=10)
    grant = models.ForeignKey(VoucherGrant,on_delete=models.PROTECT,null=True,blank=True)
    ordinal = models.PositiveIntegerField(default=1)
    snapshot = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['campaign','user'],condition=Q(audience='PUBLIC'),name='voucher_v2_public_once'),
            models.UniqueConstraint(fields=['campaign','user','ordinal'],name='voucher_v2_use_ordinal'),
            models.CheckConstraint(condition=Q(audience='PUBLIC',grant__isnull=True,ordinal=1) | Q(audience='PRIVATE',grant__isnull=False,ordinal__gte=1),name='voucher_v2_use_shape')]
