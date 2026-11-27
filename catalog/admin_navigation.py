"""Presentation-only navigation; underlying view and ModelAdmin permissions remain authoritative."""
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from .permissions import has_role


def admin_navigation(request):
    is_admin = has_role(request.user, 'ADMIN')
    result = {'admin_layout_template': 'admin/operations_shell.html' if is_admin else 'commerce/staff_operations_base.html'}
    if not is_admin:
        return result
    native = admin.site.has_permission(request)
    from commerce.models import Voucher
    groups = []
    path = request.path
    def item(label, name, args=(), aliases=(), exact=False):
        url = reverse(name, args=args)
        active = path == url if exact else any(path.startswith(p) for p in (url,) + aliases)
        return {'label': label, 'url': url, 'active': active}
    overview = []
    if native:
        overview.append(item('Tổng quan traffic', 'admin:index', exact=True))
    overview.append(item('Vận hành hôm nay', 'dashboard', exact=True))
    groups.append({'label': 'TỔNG QUAN', 'items': overview})
    groups.append({'label': 'VẬN HÀNH', 'items': [item('Xử lý đơn hàng','queue',exact=True),item('Hàng chờ pha chế','kitchen',aliases=('/dashboard/kitchen/',)),item('POS tại quầy / APP','new_manual'),item('Nhập / xuất và tồn kho','inventory'),item('Hoàn tiền mô phỏng','refunds'),item('Báo cáo','reports')]})
    merchandise = [item('Sản phẩm','reference_management',('products',),('/admin/catalog/product/',)),item('Danh mục','reference_management',('categories',),('/admin/catalog/category/',))]
    if settings.NAU_VOUCHERS_V2_ENABLED:
        merchandise.append(item('Mã giảm giá / Voucher','admin:commerce_voucher_changelist' if native and admin.site._registry[Voucher].has_view_or_change_permission(request) else 'voucher_campaigns',aliases=('/dashboard/vouchers/','/admin/commerce/voucher/','/dashboard/manage/promotions/')))
    if not settings.NAU_VOUCHERS_V2_ENABLED:
        merchandise.append(item('Mã giảm giá / Voucher','reference_management',('promotions',),('/admin/commerce/voucher/',)))
    groups.append({'label':'QUẢN LÝ CỬA HÀNG','items':merchandise})
    people = [item('Khách hàng','reference_management',('customers',)),item('Nhân viên','reference_management',('staff',))]
    if settings.NAU_CUSTOMER_ACCOUNTS_ENABLED:
        people += [item('Nhận diện khách tại quầy','customer_lookup'),item('Tạo tài khoản tại quầy','staff_customer_create')]
    groups.append({'label':'KHÁCH HÀNG & NHÂN SỰ','items':people})
    # Keep all permission-eligible models. Only replace duplicate entry points with the
    # corresponding custom list; native CRUD remains reachable from contextual links.
    replaced = {('catalog','product'),('catalog','category'),('commerce','voucher')}
    if native:
        for app in admin.site.get_app_list(request):
            links = []
            for model in app['models']:
                key = (app['app_label'], model['model']._meta.model_name)
                if key in replaced:
                    continue
                url = model.get('admin_url') or model.get('add_url')
                if not url:
                    continue
                label = str(model['name'])
                if key == ('commerce','order'):
                    label = 'Dữ liệu / lịch sử đơn hàng'
                elif key == ('support','policy'):
                    label = 'Quản lý chính sách'
                elif key == ('commerce','ingredient'):
                    label = 'Danh mục nguyên liệu'
                links.append({'label': label,'url': url,'active':path.startswith(url.removesuffix('add/'))})
            if links:
                groups.append({'label': str(app['name']), 'items':links})
    groups.append({'label':'CẤU HÌNH','items':[item('Cấu hình hệ thống','reference_configuration',('store',),('/dashboard/settings/',))]})
    current = next((entry['label'] for group in groups for entry in group['items'] if entry['active']), 'Quản trị')
    result.update(nau_admin_groups=groups,nau_admin_native=native,nau_admin_page=current,is_nav_sidebar_enabled=True)
    return result
