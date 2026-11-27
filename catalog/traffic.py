"""Small local telemetry store, isolated from business PostgreSQL and credentials."""
import fcntl
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import secrets
import stat
import time
from datetime import datetime, timedelta, timezone as utc_timezone
from urllib.parse import urlsplit
from django.conf import settings
from django.core import signing
from django.utils import timezone

COOKIE = 'nau_traffic'
SALT = 'nau.traffic.v1'
MAX_BYTES = 1024 * 1024  # Hard daily cap. Do not let telemetry grow without bound.
PATHS = {'home': '/', 'menu': '/menu/', 'product': '/products/<slug>/', 'cart': '/cart/', 'checkout': '/checkout/', 'cart_add': '/cart/add/'}


def root():
    return Path(settings.NAU_TRAFFIC_ROOT)


def private_file(path, create=False):
    folder = root()
    if create:
        folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    if folder.is_symlink() or folder.stat().st_uid != os.getuid() or folder.stat().st_mode & 0o777 != 0o700:
        raise OSError('Unsafe telemetry directory')
    fd = os.open(path, os.O_NOFOLLOW | (os.O_CREAT | os.O_RDWR if create else os.O_RDONLY), 0o600)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o777 != 0o600:
        os.close(fd)
        raise OSError('Unsafe telemetry file')
    return fd


def append(event):
    day = datetime.fromtimestamp(event['timestamp'], utc_timezone.utc).strftime('%Y-%m-%d')
    path = root() / (day + '.jsonl')
    with os.fdopen(private_file(path, True), 'r+', encoding='utf8') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0, 2)
        line = json.dumps(event, separators=(',', ':')) + '\n'
        if stream.tell() + len(line.encode()) <= MAX_BYTES:
            stream.write(line)
            stream.flush()


def events(start, end):
    folder = root()
    if not folder.exists():
        return []
    rows = []
    first = start.astimezone(utc_timezone.utc).date()
    last = end.astimezone(utc_timezone.utc).date()
    for offset in range((last - first).days + 1):
        path = folder / ((first + timedelta(days=offset)).isoformat() + '.jsonl')
        if not path.exists():
            continue
        with os.fdopen(private_file(path), encoding='utf8') as stream:
            fcntl.flock(stream, fcntl.LOCK_SH)
            for line in stream.read(MAX_BYTES).splitlines():
                try:
                    row = json.loads(line)
                    if start.timestamp() <= row['timestamp'] <= end.timestamp():
                        rows.append(row)
                except (ValueError, KeyError, TypeError):
                    continue
    return rows


def anonymous_hash(value):
    return hmac.new(settings.SECRET_KEY.encode(), ('traffic:' + value).encode(), hashlib.sha256).hexdigest()


class TrafficMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not settings.NAU_TRAFFIC_ENABLED:
            return response
        match = getattr(request, 'resolver_match', None)
        name = match.url_name if match else None
        agent = request.META.get('HTTP_USER_AGENT', '').lower()[:512]
        if name not in PATHS or any(bot in agent for bot in ('bot', 'spider', 'crawler', 'headless', 'curl', 'wget')):
            return response
        if request.method not in ('GET', 'POST') or (request.method == 'POST' and name != 'cart_add'):
            return response
        # Internal operators do not inflate customer traffic; all admin/assets/auth URLs are excluded.
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and (user.is_staff or user.is_superuser or user.groups.filter(name__in=['STAFF', 'ADMIN']).exists()):
            return response
        from support import policies
        if policies.enabled() and not policies.preference(user, 'ANALYTICS'):
            if COOKIE in request.COOKIES:response.delete_cookie(COOKIE,samesite='Lax')
            return response
        now = int(time.time())
        try:
            previous = signing.loads(request.COOKIES.get(COOKIE, ''), salt=SALT, max_age=30 * 86400)
            assert isinstance(previous, dict) and all(isinstance(previous[k], str) and len(previous[k]) == 32 for k in ('visitor', 'session'))
            assert isinstance(previous['seen'], int) and previous['seen'] <= now
        except (signing.BadSignature, ValueError, KeyError, TypeError, AssertionError):
            previous = {'visitor': secrets.token_hex(16), 'session': secrets.token_hex(16), 'seen': now}
        if now - previous['seen'] > 1800:
            previous['session'] = secrets.token_hex(16)
        previous['seen'] = now
        source = 'direct'
        try:
            host = (urlsplit(request.META.get('HTTP_REFERER', '')[:2048]).hostname or '').lower()
            if host:
                source = 'internal' if host == request.get_host().split(':')[0] else 'referral'
                if any(host == d or host.endswith('.' + d) for d in ('google.com', 'google.com.vn', 'bing.com', 'duckduckgo.com')):
                    source = 'search'
                elif any(host == d or host.endswith('.' + d) for d in ('facebook.com', 'instagram.com', 'tiktok.com', 'youtube.com')):
                    source = 'social'
        except ValueError:
            pass
        device = 'tablet' if ('ipad' in agent or ('android' in agent and 'mobile' not in agent)) else ('mobile' if any(x in agent for x in ('mobile', 'iphone')) else 'desktop')
        added = name == 'cart_add' and 200 <= response.status_code < 400 and any(m.level == 25 for m in getattr(getattr(request, '_messages', None), '_queued_messages', []))
        row = {'timestamp': now, 'path': PATHS[name], 'session': anonymous_hash(previous['session']), 'visitor': anonymous_hash(previous['visitor']), 'source': source, 'device': device, 'authenticated': bool(user and user.is_authenticated), 'status': response.status_code, 'event': 'add_cart' if added else ('page' if request.method == 'GET' else 'cart_request')}
        try:
            append(row)
            response.set_cookie(COOKIE, signing.dumps(previous, salt=SALT), max_age=30 * 86400, httponly=True, secure=request.is_secure(), samesite='Lax')
        except OSError:
            logging.getLogger(__name__).warning('Traffic storage unavailable; customer response preserved.')
        return response


def dashboard(period):
    from collections import Counter
    from django.contrib.auth import get_user_model
    from commerce.models import Order
    now = timezone.localtime()
    days = {'today': 1, '7': 7, '30': 30}.get(period, 7)
    start = (now - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    unavailable = False
    try:
        rows = events(start, now) if settings.NAU_TRAFFIC_ENABLED else []
    except OSError:
        rows, unavailable = [], True
    pages = [r for r in rows if r.get('event') == 'page' and 200 <= r.get('status', 0) < 300]
    visits = len({r['session'] for r in pages})
    orders = list(Order.objects.filter(channel='WEB', created_at__gte=start, created_at__lte=now).values_list('created_at', flat=True))
    registrations = get_user_model().objects.filter(date_joined__gte=start, date_joined__lte=now, groups__name='CUSTOMER').exclude(groups__name__in=['STAFF', 'ADMIN']).distinct().count()
    # Never mix orders from before telemetry collection with the conversion denominator.
    coverage = min((r['timestamp'] for r in pages), default=None)
    comparable_orders = sum(d.timestamp() >= coverage for d in orders) if coverage is not None else 0
    conversion = f'{comparable_orders / visits * 100:.1f}%' if visits else '—'
    buckets = list(range(24)) if days == 1 else [(start + timedelta(days=i)).date() for i in range(days)]
    key = (lambda d: timezone.localtime(d).hour) if days == 1 else (lambda d: timezone.localtime(d).date())
    counts = Counter(key(datetime.fromtimestamp(r['timestamp'], utc_timezone.utc)) for r in pages)
    # Visits deduplicated separately in every time bucket; a visit can span two buckets.
    sessions = {b: set() for b in buckets}
    for r in pages:
        sessions[key(datetime.fromtimestamp(r['timestamp'], utc_timezone.utc))].add(r['session'])
    order_counts = Counter(key(d) for d in orders)
    peak = max([len(sessions[b]) for b in buckets] + [order_counts[b] for b in buckets] + [1])
    points = lambda values: ' '.join(f'{20 + i * 760 / max(1, len(buckets)-1):.1f},{180 - v * 150 / peak:.1f}' for i, v in enumerate(values))
    def breakdown(field, labels):
        data = Counter(r[field] for r in pages)
        return [{'label': label, 'count': data[k], 'percent': round(data[k] / max(1, len(pages)) * 100)} for k, label in labels]
    # Presentation only: do not imply attribution between old orders and new visits.
    conversion = 'Chưa đủ dữ liệu'
    coverage_bucket = key(datetime.fromtimestamp(coverage, utc_timezone.utc)) if coverage else None
    covered_orders = Counter(key(d) for d in orders if coverage is not None and d.timestamp() >= coverage)
    chart = []
    for i, bucket in enumerate(buckets):
        covered = coverage_bucket is not None and bucket >= coverage_bucket and bucket <= key(now)
        chart.append({'label': f'{bucket:02d}:00' if days == 1 else bucket.strftime('%d/%m'),
                      'visits': len(sessions[bucket]) if covered else None,
                      'orders': covered_orders[bucket] if covered else None})
    chart_peak = max([item[k] or 0 for item in chart for k in ('visits','orders')] + [1])
    for i, item in enumerate(chart):
        item.update(x=55+i*710/len(chart), width=max(3,710/len(chart)*.31), tick=i % max(1,len(chart)//7)==0 or i==len(chart)-1)
        for name in ('visits','orders'):
            value=item[name] or 0
            item[name+'_height']=value/chart_peak*170
            item[name+'_y']=210-value/chart_peak*170
    return {'chart_bars':chart,'chart_peak':chart_peak,'chart_mid':round(chart_peak/2,1),'chart_coverage':datetime.fromtimestamp(coverage, utc_timezone.utc) if coverage else None, 'period': period if period in ('today','7','30') else '7', 'days': days, 'visits': visits, 'unique': len({r['visitor'] for r in pages}), 'pageviews': len(pages), 'registrations': registrations, 'orders': len(orders), 'conversion': conversion, 'empty': not pages, 'unavailable': unavailable, 'enabled': settings.NAU_TRAFFIC_ENABLED, 'from': start, 'to': now, 'visit_points': points([len(sessions[b]) for b in buckets]), 'order_points': points([order_counts[b] for b in buckets]), 'peak': peak, 'sources': breakdown('source', [('direct','Trực tiếp'),('internal','Trong website'),('search','Tìm kiếm'),('social','Mạng xã hội'),('referral','Giới thiệu')]), 'devices': breakdown('device', [('mobile','Điện thoại'),('tablet','Máy tính bảng'),('desktop','Máy tính')]), 'funnel': [('Vào website', visits),('Xem menu',len({r['session'] for r in pages if r['path']=='/menu/'})),('Thêm giỏ thành công',len({r['session'] for r in rows if r.get('event')=='add_cart'})),('Vào checkout',len({r['session'] for r in pages if r['path']=='/checkout/'})),('Đơn WEB từ khi có tracking',comparable_orders if coverage is not None else '—')], 'top_pages': Counter(r['path'] for r in pages).most_common(5), 'hours': Counter(timezone.localtime(datetime.fromtimestamp(r['timestamp'], utc_timezone.utc)).hour for r in pages).most_common(5)}
