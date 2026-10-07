# -*- coding: utf-8 -*-
"""core/time_utils.py の単体テスト。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.time_utils import normalize_time


class TestTimeUtils(unittest.TestCase):
    def test_normalize_time_valid(self):
        self.assertEqual(normalize_time("9:5"), "09:05")
        self.assertEqual(normalize_time("09:05"), "09:05")
        self.assertEqual(normalize_time("0:0"), "00:00")
        self.assertEqual(normalize_time("23:59"), "23:59")
        self.assertEqual(normalize_time(" 12:30 "), "12:30")

    def test_normalize_time_invalid(self):
        self.assertIsNone(normalize_time(""))
        self.assertIsNone(normalize_time("invalid"))
        self.assertIsNone(normalize_time("24:00"))
        self.assertIsNone(normalize_time("12:60"))
        self.assertIsNone(normalize_time("-1:00"))
        self.assertIsNone(normalize_time(None))


if __name__ == "__main__":
    unittest.main()