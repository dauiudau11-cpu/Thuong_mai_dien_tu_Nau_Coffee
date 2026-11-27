import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from catalog import traffic
from tests.test_vouchers_v2 import fixture, Helpers, SETTINGS


class TrafficCollectionTests(SimpleTestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.override = override_settings(NAU_TRAFFIC_ENABLED=True, NAU_TRAFFIC_ROOT=Path(self.temp.name)/'events')
        self.override.enable()
        self.addCleanup(self.override.disable)

    def request(self, name='menu', method='get', cookie=None, status=200, **meta):
        request = getattr(RequestFactory(), method)('/menu/?token=SECRET', **meta)
        request.resolver_match = SimpleNamespace(url_name=name)
        request.user = AnonymousUser()
        if cookie:
            request.COOKIES[traffic.COOKIE] = cookie
        return traffic.TrafficMiddleware(lambda r: HttpResponse(status=status))(request)

    def rows(self):
        now=timezone.now()
        return traffic.events(now-timezone.timedelta(days=1),now+timezone.timedelta(days=1))

    def test_safe_fields_cookie_identity_sources_and_device(self):
        first=self.request(HTTP_USER_AGENT='iPhone Mobile secret-agent',HTTP_REFERER='https://google.com/search?email=SECRET')
        self.request(cookie=first.cookies[traffic.COOKIE].value)
        rows=self.rows()
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['session'],rows[1]['session'])
        self.assertEqual(rows[0]['visitor'],rows[1]['visitor'])
        self.assertEqual((rows[0]['device'],rows[0]['source']),('mobile','search'))
        self.assertNotIn('SECRET',json.dumps(rows))
        self.assertNotIn('secret-agent',json.dumps(rows))
        self.assertEqual(rows[0]['path'],'/menu/')
        self.assertTrue(first.cookies[traffic.COOKIE]['httponly'])
        self.assertEqual(next((Path(self.temp.name)/'events').glob('*.jsonl')).stat().st_mode & 0o777,0o600)

    def test_bot_assets_auth_admin_are_not_collected(self):
        self.request(HTTP_USER_AGENT='Googlebot')
        for name in ['index','login','customer_password_reset','health','queue',None]:
            self.request(name)
        self.assertEqual(self.rows(),[])

    def test_idle_session_rotates_visitor_stays(self):
        with patch('catalog.traffic.time.time',return_value=2000000000):
            response=self.request()
        with patch('catalog.traffic.time.time',return_value=2000001900):
            request=self.request(cookie=response.cookies[traffic.COOKIE].value)
        old=traffic.signing.loads(response.cookies[traffic.COOKIE].value,salt=traffic.SALT)
        new=traffic.signing.loads(request.cookies[traffic.COOKIE].value,salt=traffic.SALT)
        self.assertEqual(old['visitor'],new['visitor'])
        self.assertNotEqual(old['session'],new['session'])

    def test_bad_cookie_and_unwritable_store_do_not_break_response(self):
        with patch('catalog.traffic.append',side_effect=OSError):
            self.assertEqual(self.request(cookie='forged').status_code,200)

    def test_cart_funnel_requires_success_message_not_just_redirect(self):
        request=RequestFactory().post('/cart/add/')
        request.user=AnonymousUser();request.resolver_match=SimpleNamespace(url_name='cart_add')
        request._messages=SimpleNamespace(_queued_messages=[])
        collector=traffic.TrafficMiddleware(lambda r:HttpResponse(status=302))
        collector(request)
        request._messages._queued_messages=[SimpleNamespace(level=25)]
        collector(request)
        self.assertEqual([r['event'] for r in self.rows()],['cart_request','add_cart'])


@override_settings(**SETTINGS)
class AdminTrafficTests(Helpers, TestCase):
    @classmethod
    def setUpTestData(cls):
        fixture(cls)
        cls.admin.is_staff=True;cls.admin.save(update_fields=['is_staff'])

    def test_admin_periods_and_empty_state_preserve_native_sections(self):
        self.client.force_login(self.admin)
        with TemporaryDirectory() as folder,override_settings(NAU_TRAFFIC_ENABLED=True,NAU_TRAFFIC_ROOT=Path(folder)/'events'):
            for period in ['today','7','30','forged']:
                response=self.client.get('/admin/',{'period':period})
                self.assertEqual(response.status_code,200)
                self.assertContains(response,'Traffic &amp; chuyển đổi')
                self.assertContains(response,'id="recent-actions-module"')
                self.assertContains(response,'id="nav-sidebar"')
                self.assertTrue(response.context['traffic']['empty'])
                self.assertEqual(response.context['traffic']['conversion'],'Chưa đủ dữ liệu')

    def test_aggregation_deduplicates_and_filters_time(self):
        now=int(timezone.now().timestamp())
        with TemporaryDirectory() as folder,override_settings(NAU_TRAFFIC_ENABLED=True,NAU_TRAFFIC_ROOT=Path(folder)/'events'):
            for path in ['/','/menu/','/checkout/']:
                traffic.append(dict(timestamp=now,path=path,session='s1',visitor='v1',event='page',status=200,source='direct',device='mobile',authenticated=False))
            traffic.append(dict(timestamp=now,path='/menu/',session='s2',visitor='v1',event='page',status=500,source='direct',device='mobile',authenticated=False))
            summary=traffic.dashboard('today')
            self.assertEqual((summary['visits'],summary['unique'],summary['pageviews']),(1,1,3))
            self.assertEqual(summary['conversion'],'Chưa đủ dữ liệu')
            self.assertEqual(summary['sources'][0]['count'],3)
            self.assertEqual(summary['devices'][0]['count'],3)

    def test_non_admin_has_no_dashboard(self):
        for user in [self.user,self.staff]:
            self.client.force_login(user)
            response=self.client.get('/admin/')
            self.assertEqual(response.status_code,302)
            self.assertIn('/admin/login/',response.url)

    def test_old_orders_are_not_compared_to_new_tracking(self):
        now=timezone.now()
        with TemporaryDirectory() as folder,override_settings(NAU_TRAFFIC_ENABLED=True,NAU_TRAFFIC_ROOT=Path(folder)/'events'):
            traffic.append(dict(timestamp=int(now.timestamp())-10,path='/',session='s',visitor='v',event='page',status=200,source='direct',device='desktop',authenticated=False))
            with patch('commerce.models.Order.objects.filter') as query:
                query.return_value.values_list.return_value=[now-timezone.timedelta(minutes=5)]
                summary=traffic.dashboard('7')
            self.assertEqual(summary['orders'],1)
            self.assertEqual(sum(b['orders'] or 0 for b in summary['chart_bars']),0)
            self.assertEqual(summary['funnel'][-1][1],0)
            self.assertEqual(summary['conversion'],'Chưa đủ dữ liệu')
