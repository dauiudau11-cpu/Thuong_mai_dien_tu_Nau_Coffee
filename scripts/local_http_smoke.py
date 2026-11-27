"""Read-only public HTTP smoke; this is not visual/browser QA."""
from urllib.request import urlopen

URLS = ['/', '/menu/', '/products/ca-phe-sua-da/', '/accounts/login/', '/accounts/register/',
        '/promotions/', '/healthz/', '/static/catalog/site.css', '/static/catalog/drink.svg']

if __name__ == '__main__':
    for path in URLS:
        with urlopen('http://127.0.0.1:8000' + path, timeout=10) as response:
            if response.status != 200:
                raise SystemExit(f'FAIL: {path}: HTTP {response.status}')
            print(f'PASS: {path}: HTTP 200')
