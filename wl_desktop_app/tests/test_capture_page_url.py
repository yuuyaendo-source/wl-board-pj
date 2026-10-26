"""顔セルフ登録はブラウザで linko-system の撮影専用画面（/capture）を開く（2026-10-26）。

アプリ内カメラ（3連写）は撮影の採点・案内・複数枚登録を通らない。受付/管理と同じ撮影 UI を使うため、
OTP 後に /capture#p=…&t=… を開く。トークンはフラグメント（サーバのアクセスログに残らない）。
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import face_registry_self_client as c


class TestCapturePageUrl(unittest.TestCase):
    def test_builds_fragment_url_and_validates_without_token(self):
        seen = []
        with mock.patch("security.validate_http_url", side_effect=lambda u, *a, **k: (seen.append(u) or (True, ""))):
            url = c.capture_page_url({"linko_server_url": "https://linkosys.example/"}, "p 1", "a.b/c")
        self.assertEqual(url, "https://linkosys.example/capture#p=p%201&t=a.b%2Fc")
        self.assertEqual(seen, ["https://linkosys.example/capture"])  # 検証にトークンを渡さない

    def test_blocked_or_missing_returns_none(self):
        with mock.patch("security.validate_http_url", return_value=(False, "blocked")):
            self.assertIsNone(c.capture_page_url({"linko_server_url": "https://evil.example"}, "p1", "t"))
        self.assertIsNone(c.capture_page_url({}, "p1", "t"))
        self.assertIsNone(c.capture_page_url({"linko_server_url": "https://x"}, "", "t"))


if __name__ == "__main__":
    unittest.main()
