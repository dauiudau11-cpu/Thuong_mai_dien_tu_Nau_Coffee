from django.core.validators import FileExtensionValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.templatetags.static import static
from django.utils import timezone
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def image_url(self):
        picture = self.images.first()
        if picture and picture.image:
            return picture.image.url
        # User-approved AI visual mockups: illustrative image fallback, not real product photography.
        if self.code in {'CF01', 'CF02', 'CF03', 'CF04', 'TE01', 'TE02', 'OT01', 'OT02'}:
            return static(f'catalog/premium/{self.code.lower()}.webp')
        return static('catalog/drink.svg')

    def __str__(self):
        return self.name


def validate_image_size(image):
    from django.core.exceptions import ValidationError
    if image.size > 5 * 1024 * 1024:
        raise ValidationError('Ảnh tối đa 5 MB.')


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', validators=[
        FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp']), validate_image_size])
    alt = models.CharField(max_length=200)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'pk']


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.PROTECT)
    sku = models.CharField(max_length=30, unique=True)
    size = models.CharField(max_length=10, choices=[('STANDARD', 'Chuẩn'), ('M', 'M'), ('L', 'L'), ('FIXED', 'Chuẩn')])
    volume_ml = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    is_available = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['product', 'size'], name='unique_product_size')]

    def __str__(self):
        if self.size == 'FIXED':
            return f'{self.product.name} / {self.volume_ml} ml'
        return f'{self.product.name} / {self.size}'


class ProductOption(models.Model):
    product = models.ForeignKey(Product, related_name='options', on_delete=models.PROTECT)
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=10, choices=[('SUGAR', 'Đường'), ('ICE', 'Đá'), ('TOPPING', 'Topping')])
    price_delta = models.PositiveBigIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['product', 'kind', 'name'], name='unique_product_option')]

    def __str__(self):
        return f'{self.product.name}: {self.name}'


class ChannelPrice(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='prices', on_delete=models.CASCADE)
    channel = models.CharField(max_length=10, choices=[('WEB', 'Website'), ('COUNTER', 'Quầy'), ('APP', 'Ứng dụng demo')])
    original_price = models.PositiveBigIntegerField()
    sale_price = models.PositiveBigIntegerField(null=True, blank=True)
    sale_starts_at = models.DateTimeField(null=True, blank=True)
    sale_ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['variant', 'channel'], name='unique_variant_channel'),
            models.CheckConstraint(condition=Q(sale_price__isnull=True) | (
                Q(sale_price__lt=models.F('original_price')) & Q(sale_starts_at__isnull=False)
                & Q(sale_ends_at__isnull=False) & Q(sale_ends_at__gt=models.F('sale_starts_at'))), name='valid_sale'),
        ]

    @property
    def current_price(self):
        now = timezone.now()
        if (self.sale_price is not None and self.sale_starts_at and self.sale_ends_at
                and self.sale_starts_at <= now < self.sale_ends_at):
            return self.sale_price
        return self.original_price

    def __str__(self):
        return f'{self.variant.sku} / {self.channel}'


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='addresses', on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    recipient = models.CharField(max_length=100)
    phone = models.CharField(max_length=30)
    text = models.TextField(max_length=500)

    def __str__(self):
        return self.label


class StandardCost(models.Model):
    """Approved per-drink cost; not a substitute for inventory BOM."""
    variant = models.OneToOneField(ProductVariant, on_delete=models.PROTECT, related_name='standard_cost')
    ingredient_cost = models.PositiveBigIntegerField()

    class Meta:
        constraints = [models.CheckConstraint(condition=Q(ingredient_cost__gte=0), name='standard_cost_nonnegative')]

# Models are installed for migration discovery; queries remain behind the rollout flag.
from .customer_models import CustomerProfile, CounterConsent, CounterCustomerLink  # noqa: E402,F401
