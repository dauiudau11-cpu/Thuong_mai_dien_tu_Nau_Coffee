"""Presentation helpers only; never change stored prices or role permissions."""
from decimal import Decimal, InvalidOperation
from django import template
from catalog.permissions import effective_role, has_role

register = template.Library()


@register.filter
def vnd(value):
    """Format integer VND without locale-dependent grouping or float arithmetic."""
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount != amount.to_integral_value():
            return '—'
        return format(int(amount), ',').replace(',', '.') + ' đ'
    except (InvalidOperation, ValueError, TypeError):
        return '—'


@register.filter
def role(user, name):
    # Navigation visibility only. Views/services remain the authorization boundary.
    return has_role(user, name)


@register.filter
def login_role(user):
    return effective_role(user) or ''


@register.simple_tag(takes_context=True)
def query_update(context, **changes):
    """Change a filter without discarding search/price/sort, and reset pagination."""
    query = context['request'].GET.copy()
    query.pop('page', None)
    for key, value in changes.items():
        if value == '' or value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return '?' + query.urlencode()


@register.simple_tag
def cart_line(quote, item_id):
    return next((row for row in (quote or {}).get('rows', []) if row['item'].pk == item_id), None)


@register.filter
def vi_state(value):
    from catalog.localization import display_value
    return display_value(value)


@register.filter
def customer_state(value):
    return {'PENDING_PAYMENT':'Đang chờ thanh toán','PENDING_CONFIRMATION':'Đơn hàng đang chờ xác nhận',
        'CONFIRMED':'Nâu đã nhận đơn của bạn','PREPARING':'Nâu đang chuẩn bị món',
        'READY':'Món của bạn đã sẵn sàng','PICKUP_WAITING':'Mời bạn đến nhận món',
        'COMPLETED':'Đơn hàng đã hoàn thành','CANCELLED':'Đơn hàng đã được hủy'}.get(str(value), vi_state(value))


@register.filter
def vi_text(value):
    from catalog.localization import FIELD_LABELS, display_value
    return FIELD_LABELS.get(str(value), display_value(value))


@register.simple_tag
def vi_admin_label(field):
    from catalog.localization import FIELD_LABELS
    from django.utils.html import format_html
    if field.is_readonly:
        label = FIELD_LABELS.get(field.field['name'], field.field['label'])
        return format_html('<label>{}:</label>', label)
    return field.label_tag()


@register.filter
def vi_notice(value):
    """Translate system notice terminology only at render time, never saved history."""
    import re
    text = str(value)
    vocabulary = {'MOCK_ONLINE':'thanh toán trực tuyến mô phỏng', 'Kanban':'bảng hàng chờ',
        'Admin':'quản trị viên', 'Staff':'nhân viên', 'checkout':'bước thanh toán',
        'recipe snapshot':'công thức tại thời điểm đặt', 'snapshot':'bản ghi tại thời điểm đặt',
        'voucher':'mã giảm giá', 'bill':'phiếu', 'online':'trực tuyến', 'demo':'mô phỏng', 'Demo':'mô phỏng', 'DEMO':'mô phỏng'}
    for source, target in vocabulary.items():
        text = re.sub(r'(?<![\w-])' + re.escape(source) + r'(?![\w-])', lambda match: target, text)
    return text


@register.simple_tag
def vi_admin_contents(field):
    from catalog.localization import display_value, object_label
    from django.db.models import Model
    from django.utils.html import escape
    from django.utils.safestring import mark_safe
    if not field.is_readonly:
        return ''
    name = field.field['name']
    value = getattr(field.form.instance, name, None)
    contents = field.contents()
    if name in ('from_state', 'to_state', 'event_key', 'method', 'status', 'channel'):
        return display_value(value)
    if isinstance(value, Model):
        # Preserve native related-object links and escaping; replace only their caption.
        return mark_safe(str(contents).replace(str(escape(str(value))), str(escape(object_label(value)))))
    return contents


@register.filter
def vi_object(value):
    from catalog.localization import object_label
    return object_label(value) if hasattr(value, '_meta') else value
