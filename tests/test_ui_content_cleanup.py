import re
from django.test import TestCase, override_settings
from tests.test_vouchers_v2 import fixture, Helpers, SETTINGS


def visible_text(content):
    text=content.decode()
    text=re.sub(r'<script\b[^>]*>.*?</script>','',text,flags=re.S)
    return re.sub('<[^>]+>',' ',text)


@override_settings(**SETTINGS)
class UIContentCleanupTests(Helpers,TestCase):
    @classmethod
    def setUpTestData(cls):fixture(cls)

    def test_public_copy_has_no_placeholder_notes(self):
        for path in ['/','/menu/',f'/products/{self.variant.product.slug}/','/contact/','/delivery-partners/']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,200)
            text=visible_text(response.content).lower()
            for term in ['minh họa','chưa chốt','chưa được chốt','đồ án','legacy']:
                self.assertNotIn(term,text,path)

    def test_payment_remains_explicitly_simulated(self):
        order=self.place();self.client.force_login(self.user)
        response=self.client.get(f'/payments/mock/{order.payment.token}/')
        text=visible_text(response.content).lower()
        self.assertIn('mô phỏng',text);self.assertIn('không thu tiền thật',text)
        self.assertNotIn('đồ án',text)
        response=self.client.get(f'/account/orders/{order.public_code}/')
        self.assertNotIn('demo',visible_text(response.content).lower())

    def test_partner_and_store_uncertainty_is_not_hidden(self):
        text=visible_text(self.client.get('/delivery-partners/').content).lower()
        self.assertIn('chưa xác nhận',text)
        self.assertIn('không được chuyển',text)
        text=visible_text(self.client.get('/contact/').content).lower()
        self.assertIn('457/9 điện biên phủ',text)
        self.assertIn('0824672384',text)
        self.assertIn('<iframe',self.client.get('/contact/').content.decode())

    def test_one_menu_and_old_urls_use_same_workspace(self):
        self.client.force_login(self.admin)
        for path in ['/dashboard/vouchers/','/dashboard/manage/promotions/']:
            response=self.client.get(path)
            self.assertEqual(response.status_code,200)
            self.assertTemplateUsed(response,'commerce/voucher_campaigns.html')
            self.assertNotIn('legacy',visible_text(response.content).lower())
