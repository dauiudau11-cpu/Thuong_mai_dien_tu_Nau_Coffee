"""Offline, deterministic delivery demo. Distances are FIXTURES, not real road distances.

No Google Maps, network call, GPS, or customer-data lookup. Unknown inputs fail closed.
"""
from dataclasses import dataclass
from datetime import timedelta
import unicodedata

from catalog.store_identity import STORE

STORE_ADDRESS = STORE['address']
MAX_DISTANCE_METERS = 3000
DELIVERY_FEE_VND = 25_000
FREE_SHIPPING_OVER_VND = 200_000
DELIVERY_SLA = timedelta(minutes=60)


class DemoDeliveryError(ValueError):
    """Address is not one of the explicitly supported demonstration fixtures."""


@dataclass(frozen=True)
class DemoLocation:
    key: str
    label: str
    distance_meters: int
    aliases: tuple[str, ...]


# These deliberately fictional text addresses have assigned FAKE distances.
# Do not describe them as verified Google Maps routes or physical locations.
LOCATIONS = (
    DemoLocation('A', 'Địa chỉ demo A', 2400, ('Địa chỉ demo A', 'DEMO-A', 'demo a')),
    DemoLocation('B', 'Địa chỉ demo B', 3600, ('Địa chỉ demo B', 'DEMO-B', 'demo b')),
)


def normalize_address(value: str) -> str:
    if not isinstance(value, str):
        raise DemoDeliveryError('Địa chỉ giao hàng không hợp lệ.')
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def find_demo_location(address: str) -> DemoLocation:
    key = normalize_address(address)
    for location in LOCATIONS:
        if key in {normalize_address(alias) for alias in location.aliases}:
            return location
    raise DemoDeliveryError('Địa chỉ chưa có trong bộ dữ liệu mô phỏng. Hãy nhập Địa chỉ demo A hoặc Địa chỉ demo B.')


def shipping_fee_vnd(distance_meters: int, net_goods_vnd: int) -> int:
    """Fail closed for out-of-radius; threshold is STRICTLY greater than 200k."""
    if isinstance(distance_meters, bool) or not isinstance(distance_meters, int) or distance_meters < 0:
        raise DemoDeliveryError('Khoảng cách mô phỏng không hợp lệ.')
    if isinstance(net_goods_vnd, bool) or not isinstance(net_goods_vnd, int) or net_goods_vnd < 0:
        raise DemoDeliveryError('Tiền hàng không hợp lệ.')
    if distance_meters > MAX_DISTANCE_METERS:
        raise DemoDeliveryError('Địa chỉ nằm ngoài phạm vi giao hàng 3 km. Vui lòng chọn nhận tại quán.')
    return 0 if net_goods_vnd > FREE_SHIPPING_OVER_VND else DELIVERY_FEE_VND


@dataclass(frozen=True)
class DemoDeliveryQuote:
    address_label: str
    location_key: str
    distance_meters: int
    shipping_vnd: int


def quote_demo_delivery(address: str, subtotal_vnd: int, discount_vnd: int) -> DemoDeliveryQuote:
    if (isinstance(subtotal_vnd, bool) or isinstance(discount_vnd, bool)
            or not isinstance(subtotal_vnd, int) or not isinstance(discount_vnd, int)
            or subtotal_vnd < 0 or not 0 <= discount_vnd <= subtotal_vnd):
        raise DemoDeliveryError('Tiền hàng hoặc voucher không hợp lệ.')
    location = find_demo_location(address)
    fee = shipping_fee_vnd(location.distance_meters, subtotal_vnd - discount_vnd)
    return DemoDeliveryQuote(location.label, location.key, location.distance_meters, fee)


def delivery_deadline(bill_issued_at):
    if bill_issued_at is None:
        raise ValueError('Chưa có thời điểm xuất bill.')
    return bill_issued_at + DELIVERY_SLA


def delivery_late(bill_issued_at, completed_at=None, *, now=None):
    """Exact boundary is ON TIME; cancelled orders must be excluded by caller."""
    if bill_issued_at is None:
        return False
    if completed_at is None and now is None:
        raise ValueError('Cần cung cấp thời điểm kiểm tra.')
    return (completed_at if completed_at is not None else now) > delivery_deadline(bill_issued_at)
