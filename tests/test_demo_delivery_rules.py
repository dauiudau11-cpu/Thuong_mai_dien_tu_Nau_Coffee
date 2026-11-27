"""Pure rule tests. Run: python3 -m unittest discover -s tests -p test_demo_delivery_rules.py"""
import unittest
from datetime import datetime, timedelta, timezone
from commerce.demo_delivery import (
    DemoDeliveryError, find_demo_location, quote_demo_delivery,
    shipping_fee_vnd, delivery_deadline, delivery_late,
)


class DemoDeliveryRuleTests(unittest.TestCase):
    def test_inside_radius_ship_25k(self):
        q = quote_demo_delivery('  ĐỊA CHỈ   DEMO A  ', 150000, 0)
        self.assertEqual((q.distance_meters, q.shipping_vnd), (2400, 25000))

    def test_outside_radius_is_rejected(self):
        with self.assertRaises(DemoDeliveryError):
            quote_demo_delivery('Địa chỉ demo B', 300000, 0)

    def test_order_300k_is_freeship(self):
        self.assertEqual(quote_demo_delivery('DEMO-A', 300000, 0).shipping_vnd, 0)

    def test_exact_distance_limit(self):
        self.assertEqual(shipping_fee_vnd(3000, 100000), 25000)
        with self.assertRaises(DemoDeliveryError):
            shipping_fee_vnd(3001, 100000)

    def test_strict_free_shipping_threshold(self):
        self.assertEqual(shipping_fee_vnd(2400, 199999), 25000)
        self.assertEqual(shipping_fee_vnd(2400, 200000), 25000)
        self.assertEqual(shipping_fee_vnd(2400, 200001), 0)

    def test_discount_applied_before_free_shipping(self):
        self.assertEqual(quote_demo_delivery('Địa chỉ demo A', 300000, 110000).shipping_vnd, 25000)
        self.assertEqual(quote_demo_delivery('Địa chỉ demo A', 300000, 99999).shipping_vnd, 0)

    def test_unknown_input_is_rejected(self):
        for address in ('', 'Địa chỉ thật bất kỳ', 'Địa chỉ demo A, thêm ký tự'):
            with self.subTest(address=address), self.assertRaises(DemoDeliveryError):
                find_demo_location(address)

    def test_bad_financial_values_are_rejected(self):
        for subtotal, discount in [(100, 101), (-1, 0), (100, -1), (True, 0), (100, 1.5)]:
            with self.subTest(subtotal=subtotal, discount=discount), self.assertRaises(DemoDeliveryError):
                quote_demo_delivery('DEMO-A', subtotal, discount)

    def test_bill_deadline_60_minutes_and_early_or_late(self):
        issued = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)
        self.assertEqual(delivery_deadline(issued), issued + timedelta(minutes=60))
        self.assertFalse(delivery_late(issued, issued + timedelta(minutes=35)))
        self.assertFalse(delivery_late(issued, issued + timedelta(minutes=60)))
        self.assertTrue(delivery_late(issued, issued + timedelta(minutes=60, seconds=1)))


if __name__ == '__main__':
    unittest.main()
