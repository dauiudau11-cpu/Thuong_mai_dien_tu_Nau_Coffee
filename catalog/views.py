import unicodedata

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Case, F, OuterRef, Subquery, When
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Category, Product, ChannelPrice
from .permissions import customer_required, roles_required
from .approved_menu import enabled


def customer_catalog():
    """Shared display projection of existing WEB prices; never changes stored pricing."""
    from django.db.models import BigIntegerField
    now = timezone.now()
    prices = ChannelPrice.objects.filter(channel='WEB', variant__product=OuterRef('pk'))
    prices = prices.filter(variant__size='FIXED') if enabled() else prices.filter(variant__is_available=True)
    prices = prices.annotate(effective=Case(When(
            sale_price__isnull=False, sale_starts_at__lte=now, sale_ends_at__gt=now,
            then=F('sale_price')), default=F('original_price'), output_field=BigIntegerField()))
    prices = prices.order_by('effective', 'pk')
    return Product.objects.filter(is_active=True, category__is_active=True).select_related('category').annotate(
        menu_price_effective=Subquery(prices.values('effective')[:1]),
        card_original_price=Subquery(prices.values('original_price')[:1]),
        card_sale_ends=Subquery(prices.values('sale_ends_at')[:1])).prefetch_related('images')


def home(request):
    """Approved Cafe Premium storefront with DB-backed prices; never hardcode WEB price."""
    from commerce.models import Voucher
    from commerce.vouchers import public_campaigns
    from support.models import Review
    now = timezone.now()
    return render(request, 'catalog/home.html', {
        'products': customer_catalog().filter(menu_price_effective__isnull=False).order_by('-is_featured', 'pk')[:8],
        'categories': Category.objects.filter(is_active=True),
        'vouchers': public_campaigns(Voucher.objects.filter(is_active=True, starts_at__lte=now, ends_at__gt=now))[:2],
        'reviews': Review.objects.filter(status='APPROVED').select_related('user', 'product')[:3],
    })


def about(request):
    """Customer-facing brand story; store details come from shared context."""
    return render(request, 'catalog/about.html')


def menu(request):
    # Server-owned session timestamp; client input is never trusted for the 35-minute rule.
    entered = request.session.get('menu_entered_at')
    try:
        age = timezone.now() - timezone.datetime.fromisoformat(entered) if entered else None
    except (TypeError, ValueError):
        age = None
    if age is None or age.total_seconds() < 0 or age.total_seconds() > 4 * 3600:
        request.session['menu_entered_at'] = timezone.now().isoformat()
    products = customer_catalog()
    products = products.filter(menu_price_effective__isnull=False)
    query = request.GET.get('q', '').strip()[:150]
    if query:
        def search_key(value):
            value = unicodedata.normalize('NFD', value.casefold().replace('đ', 'd'))
            return ' '.join(''.join(char for char in value if unicodedata.category(char) != 'Mn').split())
        needle = search_key(query)
        compact = needle.replace(' ', '')
        matching = [pk for pk, name in products.values_list('pk', 'name')
                    if needle in search_key(name) or compact in search_key(name).replace(' ', '')]
        products = products.filter(pk__in=matching)
    if request.GET.get('category'):
        products = products.filter(category__slug=request.GET['category'])
    for key, lookup in [('min_price', 'gte'), ('max_price', 'lte')]:
        value = request.GET.get(key, '')
        if value.isascii() and value.isdecimal() and len(value) < 12:
            products = products.filter(**{f'menu_price_effective__{lookup}': int(value)})
    order = {'price_asc': 'menu_price_effective', 'price_desc': '-menu_price_effective',
             'name': 'name', 'name_desc': '-name', 'newest': '-created_at'}.get(request.GET.get('sort'), 'name')
    page = Paginator(products.order_by(order, 'pk').prefetch_related('images'), 8).get_page(request.GET.get('page'))
    parameters = request.GET.copy()
    parameters.pop('page', None)
    clear_search = parameters.copy()
    clear_search.pop('q', None)
    return render(request, 'catalog/menu.html', {'page_obj': page,
        'categories': Category.objects.filter(is_active=True), 'querystring': parameters.urlencode(),
        'clear_search_querystring': clear_search.urlencode(), 'search_query': query})


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True, category__is_active=True)
    prices = ChannelPrice.objects.filter(variant__product=product, channel='WEB').select_related('variant')
    prices = prices.filter(variant__size='FIXED') if enabled() else prices.filter(variant__is_available=True)
    from commerce.models import OrderItem
    from support.forms import ReviewForm
    reviews = product.reviews.filter(status='APPROVED').select_related('user')
    eligible = OrderItem.objects.filter(order__user=request.user, order__status='COMPLETED',
        variant__product=product, review__isnull=True) if request.user.is_authenticated else OrderItem.objects.none()
    return render(request, 'catalog/product.html', {'product': product, 'prices': prices,
        'standard_can_order': prices.filter(variant__is_available=True).exists(),
        'reviews': Paginator(reviews, 5).get_page(request.GET.get('page')),
        'eligible_items': eligible, 'review_form': ReviewForm(),
        'related_products': customer_catalog().filter(category=product.category, menu_price_effective__isnull=False).exclude(pk=product.pk).order_by('pk')[:4]})


def register(request):
    from .customer_accounts import enabled
    if enabled():
        from .customer_views import register as customer_register
        return customer_register(request)
    from support.policies import enabled as policies_enabled
    if policies_enabled():
        from django.http import HttpResponse
        return HttpResponse('Đăng ký đang được chuẩn bị. Vui lòng quay lại sau.',status=503)
    return legacy_register(request)


@transaction.atomic
def legacy_register(request):
    form = UserCreationForm(request.POST or None)
    from support.services import allow_submission
    if request.method == 'POST' and not allow_submission(request, 'register', limit=10):
        form = UserCreationForm(data={})
        form.add_error(None, 'Quá nhiều lần đăng ký. Vui lòng thử lại sau 10 phút.')
        return render(request, 'registration/register.html', {'form': form}, status=429)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        group, _ = Group.objects.get_or_create(name='CUSTOMER')
        user.groups.add(group)
        return redirect('login')
    return render(request, 'registration/register.html', {'form': form})


@customer_required
def account(request):
    return render(request, 'catalog/account.html')


@roles_required('STAFF', 'ADMIN')
def dashboard(request):
    """Read-only operational figures for the premium dashboard, never screenshot mock values."""
    from django.db.models import Sum
    from django.utils import timezone
    from commerce.models import Order, OrderItem, Payment, Ingredient
    from .models import ProductVariant
    from .permissions import has_role
    today = timezone.localdate()
    today_orders = Order.objects.filter(created_at__date=today)
    active = [Order.Status.CONFIRMED, Order.Status.PREPARING, Order.Status.READY, Order.Status.PICKUP_WAITING]
    queue = (Order.objects.filter(status__in=active).select_related('payment')
             .prefetch_related('items').order_by('-created_at')[:6])
    collected = (Payment.objects.filter(status=Payment.Status.PAID, paid_at__date=today)
                 .aggregate(amount=Sum('amount'))['amount'] or 0)
    low_stock = []
    for ingredient in Ingredient.objects.filter(is_active=True).annotate(stock=Sum('movements__delta')).order_by('sku'):
        ingredient.available_stock = ingredient.stock or 0
        if ingredient.available_stock <= ingredient.low_stock_threshold:
            low_stock.append(ingredient)
        if len(low_stock) >= 4:
            break
    popular = (OrderItem.objects.filter(order__created_at__date=today)
               .exclude(order__status=Order.Status.CANCELLED).values('product_name')
               .annotate(quantity=Sum('quantity')).order_by('-quantity', 'product_name')[:3])
    pos_items, seen = [], set()
    variants = (ProductVariant.objects.filter(is_available=True, product__is_active=True,
                product__category__is_active=True).select_related('product')
                .prefetch_related('prices', 'product__images').order_by('product_id', 'pk'))
    for variant in variants:
        if variant.product_id in seen:
            continue
        price = next((p.current_price for p in variant.prices.all() if p.channel == 'COUNTER'), None)
        if price is not None:
            pos_items.append({'product': variant.product, 'price': price})
            seen.add(variant.product_id)
        if len(pos_items) >= 8:
            break
    return render(request, 'catalog/dashboard.html', {
        'can_admin': has_role(request.user, 'ADMIN'), 'today': today,
        'new_orders': today_orders.filter(status=Order.Status.CONFIRMED).count(),
        'preparing_orders': today_orders.filter(status=Order.Status.PREPARING).count(),
        'ready_orders': today_orders.filter(status=Order.Status.READY).count(),
        'collected': collected, 'queue': queue, 'low_stock': low_stock,
        'popular': popular, 'pos_items': pos_items,
    })


def health(request):
    return JsonResponse({'status': 'ok', 'mode': 'DEMO'})
