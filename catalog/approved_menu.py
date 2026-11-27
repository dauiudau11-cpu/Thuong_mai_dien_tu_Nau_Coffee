"""Approved catalog values, in integer VND. Never called automatically on startup."""
from django.conf import settings
from django.core.exceptions import ValidationError

MENU = (
    ('CF01', 'Cà phê đen', 360, 7000, 28000, 37000),
    ('CF02', 'Cà phê sữa', 360, 8000, 32000, 43000),
    ('CF03', 'Bạc xỉu', 360, 8250, 33000, 44000),
    ('CF04', 'Cold Brew', 500, 10000, 40000, 54000),
    ('TE01', 'Trà đào', 700, 9500, 38000, 51000),
    ('TE02', 'Trà chanh', 700, 8500, 34000, 46000),
    ('OT01', 'Matcha', 700, 12250, 49000, 66000),
    ('OT02', 'Cacao sữa', 700, 11500, 46000, 62000),
)


def enabled():
    return settings.NAU_STANDARD_MENU_ENABLED


def check_channel_price(variant):
    """Fail closed if channel records drift; never silently use a different channel."""
    if enabled():
        prices = {p.channel: p for p in variant.prices.all()}
        if (set(prices) != {'WEB', 'COUNTER', 'APP'} or
                prices['WEB'].original_price != prices['COUNTER'].original_price or
                any(p.sale_price is not None for p in prices.values())):
            raise ValidationError('Giá theo kênh chưa đồng nhất; vui lòng liên hệ quản trị.')
