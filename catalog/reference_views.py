"""Drive-inspired read projections. Mutations remain in existing audited workflows."""
from django.conf import settings
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from commerce.models import Order, StoreSettings, Voucher
from support.models import Message, Review
from .models import Product, Category
from .permissions import roles_required
from .approved_menu import enabled
from .localization import display_value
from .templatetags.nau_ui import vnd


@roles_required('STAFF', 'ADMIN')
@require_GET
def kitchen(request):
    from commerce.staff import board
    return board(request)


MANAGEMENT = {
    'products': ('Sản phẩm', Product, 'catalog_product', ['Mã', 'Sản phẩm', 'Danh mục', 'SKU / dung tích hiện tại', 'Chi phí nguyên liệu', 'Giá quầy hiện tại', 'Giá ứng dụng hiện tại', 'Trạng thái']),
    'categories': ('Danh mục', Category, 'catalog_category', ['Danh mục', 'Số sản phẩm', 'Trạng thái']),
    'promotions': ('Khuyến mãi', Voucher, 'commerce_voucher', ['Mã', 'Loại', 'Giá trị', 'Từ ngày', 'Đến ngày', 'Trạng thái']),
    'customers': ('Khách hàng', User, 'auth_user', ['Tài khoản', 'Tên', 'Trạng thái']),
    'staff': ('Nhân viên', User, 'auth_user', ['Tài khoản', 'Tên', 'Vai trò', 'Trạng thái']),
}


@roles_required('ADMIN')
@require_GET
def management(request, section):
    if section == 'promotions' and settings.NAU_VOUCHERS_V2_ENABLED:
        from commerce.voucher_management import index
        return index(request)
    if section not in MANAGEMENT:
        raise Http404
    title, model, admin_name, headers = MANAGEMENT[section]
    query = request.GET.get('q', '').strip()[:150]
    items = model.objects.all().order_by('pk')
    if section == 'products':
        items = items.select_related('category').prefetch_related('images', 'variants__prices')
        if query:
            items = items.filter(Q(name__icontains=query) | Q(code__icontains=query))
    elif section == 'categories':
        items = items.annotate(product_count=Count('product'))
        if query:
            items = items.filter(name__icontains=query)
    elif section == 'promotions':
        if query:
            items = items.filter(code__icontains=query)
    else:
        role_names = ['CUSTOMER'] if section == 'customers' else ['STAFF', 'ADMIN']
        items = items.filter(groups__name__in=role_names).distinct().prefetch_related('groups')
        if query:
            items = items.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))
    state = request.GET.get('active', '')
    if state in ('yes', 'no'):
        items = items.filter(is_active=state == 'yes')
    page = Paginator(items, 20).get_page(request.GET.get('page'))
    rows = []
    for item in page:
        state_label = 'Đang hoạt động' if item.is_active else 'Tạm ngừng'
        if section == 'products':
            variants = list(item.variants.all())
            if enabled():
                variants = [v for v in variants if v.size == 'FIXED']
            def channel_prices(channel):
                from .templatetags.nau_ui import vnd
                return ' · '.join(f'{variant.sku}: {vnd(price.current_price)}' for variant in variants
                                  for price in variant.prices.all() if price.channel == channel) or 'Chưa có'
            volumes = ' · '.join(f'{variant.sku}: {variant.volume_ml} ml' for variant in variants)
            cost_text = 'Chưa có dữ liệu chi phí'
            if enabled():
                from .models import StandardCost
                cost_text = ' · '.join(vnd(c.ingredient_cost) for c in StandardCost.objects.filter(variant__in=variants)) or cost_text
            cells = [item.code, item.name, item.category.name, volumes, cost_text,
                     channel_prices('COUNTER'), channel_prices('APP'), state_label]
        elif section == 'categories':
            cells = [item.name, item.product_count, state_label]
        elif section == 'promotions':
            cells = [item.code, item.get_kind_display(), item.amount, item.starts_at, item.ends_at, state_label]
        elif section == 'staff':
            cells = [item.username, item.get_full_name(), ', '.join(str(display_value(g.name)) for g in item.groups.all()), state_label]
        else:
            cells = [item.username, item.get_full_name(), state_label]
        rows.append({'cells': cells, 'image': item.image_url if section == 'products' else '',
                     'edit': reverse(f'admin:{admin_name}_change', args=[item.pk])})
    return render(request, 'reference/management.html', {'title': title, 'section': section, 'rows': rows,
        'headers': headers, 'page_obj': page, 'add_url': reverse(f'admin:{admin_name}_add'),
        'admin_url': reverse(f'admin:{admin_name}_changelist')})


CONFIG_TABS = [('store', 'Thông tin chung'), ('appearance', 'Giao diện'), ('payment', 'Thanh toán'),
               ('delivery', 'Giao hàng'), ('notifications', 'Thông báo'), ('security', 'Bảo mật & sao lưu')]


@roles_required('ADMIN')
@require_GET
def configuration(request, section):
    if section not in dict(CONFIG_TABS):
        raise Http404
    # An unsaved default object is a projection, never get_or_create on a GET.
    stored = StoreSettings.objects.order_by('pk').first()
    operations = stored or StoreSettings()
    panels = []
    if section == 'store':
        from .store_identity import STORE
        panels = [('Thông tin cửa hàng', [('Thương hiệu', STORE['name']), ('Địa chỉ', STORE['address']),
                  ('Liên hệ', STORE['phone']), ('Email', STORE['email']), ('Google Maps', STORE['maps']), ('Giờ mở cửa tham khảo', operations.opens_at), ('Giờ đóng cửa tham khảo', operations.closes_at)]),
                  ('Logo & hình ảnh', [('Logo', 'NÂU COFFEE'), ('Ảnh sản phẩm', 'Ảnh hiện có'), ('Thay logo/ảnh bìa từ quản trị', 'Chưa hỗ trợ thay ảnh bìa')])]
    elif section == 'appearance':
        panels = [('Hệ màu đã chọn', [('Espresso', '#301C11'), ('Kem sáng', '#F8F1E9'), ('Olive', '#6C7452')]),
                  ('Chữ & hiển thị', [('Tiêu đề', 'Noto Serif'), ('Nội dung', 'Be Vietnam Pro'), ('Bố cục', 'Giao diện thích ứng máy tính, máy tính bảng và điện thoại'), ('Đổi giao diện / ảnh bìa trực tuyến', 'Chưa hỗ trợ đổi giao diện trực tuyến')])]
    elif section == 'payment':
        panels = [('Phương thức thanh toán', [('Đơn WEB mới', 'Chỉ thanh toán trực tuyến mô phỏng'), ('Quầy / đơn cũ', 'Ghi nhận tiền mặt mô phỏng; không dùng cho bước thanh toán website'), ('Đơn APP', 'Đối soát bên ngoài mô phỏng'), ('Chuyển khoản / cổng thật', 'Chưa tích hợp')]),
                  ('Giá theo kênh', [('COUNTER / APP', 'Theo bảng giá kênh hiện tại'), ('WEB', 'Theo giá máy chủ; chỉ nhận tại quán, phí giao 0 đ'), ('Giá cuối', 'Tính lại khi xác nhận đơn'), ('Hoàn tiền', 'Quản trị viên xử lý, mô phỏng')])]
    elif section == 'delivery':
        panels = [('Nhận món trên website', [('Đơn WEB mới', 'Chỉ đặt trước và nhận tại quán'), ('Phí giao WEB', '0 đ'), ('Giao tận nơi', 'Liên kết nền tảng bên ngoài; chưa xác nhận gian hàng'), ('Thời gian chuẩn bị tối thiểu', f'{operations.lead_minutes} phút')]),
                  ('Lịch nhận tự động', [('Múi giờ', 'Asia/Ho_Chi_Minh'), ('Bước lịch', '15 phút; chọn sớm nhất còn chỗ'), ('Số ngày tối đa', operations.preorder_days), ('Số đơn mỗi khung giờ', operations.slot_capacity)]),
                  ('Cấu hình lưu trữ cho đơn giao cũ — không áp dụng WEB mới', [('Phạm vi cũ', '≤3 km, nhân viên xác minh thủ công'), ('Phí giao cũ', vnd(operations.delivery_fee)), ('Ngưỡng miễn phí cũ', vnd(operations.free_delivery_min)), ('API đối tác / GPS', 'Chưa tích hợp')])]
    elif section == 'notifications':
        panels = [('Hàng đợi hiện tại', [('Đơn đã xác nhận', Order.objects.filter(status='CONFIRMED').count()), ('Đánh giá chờ duyệt', Review.objects.filter(status='PENDING').count()), ('Liên hệ / phản hồi mới', Message.objects.filter(status='NEW').count())]),
                  ('Kênh thông báo', [('Trong website', 'Thông báo và hàng đợi hiện có'), ('Thư điện tử / tin nhắn / thông báo tự động', 'Chưa triển khai'), ('Kho theo lô / hạn dùng', 'Chưa hỗ trợ quản lý hạn dùng')])]
    else:
        panels = [('Quyền truy cập', [('Đặt hàng', 'Bắt buộc đăng nhập'), ('Quản trị', 'Quản trị viên và quyền Django phía máy chủ'), ('Bảo vệ chống giả mạo yêu cầu (CSRF)', 'Có' if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE else 'Không'), ('Cookie phiên chỉ truy cập qua HTTP', settings.SESSION_COOKIE_HTTPONLY)]),
                  ('Phiên & sao lưu', [('Thời hạn phiên (giây)', settings.SESSION_COOKIE_AGE), ('Cookie HTTPS bắt buộc', settings.SESSION_COOKIE_SECURE), ('Sao lưu tự động', 'Chưa xác minh lịch chạy'), ('Khôi phục từ giao diện', 'Chưa triển khai; cần phê duyệt và kiểm chứng bản sao lưu')])]
    return render(request, 'reference/configuration.html', {'tabs': CONFIG_TABS, 'section': section,
        'panels': [{'title': title, 'rows': rows} for title, rows in panels], 'stored': bool(stored)})
