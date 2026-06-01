# -*- coding: utf-8 -*-
"""security.py のユニットテスト。"""
import os
import unittest

# テスト中は常に allowlist 有効
os.environ.pop("WLINKO_DISABLE_URL_ALLOWLIST", None)

from security import (  # noqa: E402
    is_host_allowed,
    sanitize_config_urls,
    validate_http_url,
    validate_msi_download_url,
    validate_update_check_url,
)


class TestSecurity(unittest.TestCase):
    def test_internal_host_allowed(self):
        self.assertTrue(is_host_allowed("wl-ai-board.internal.wonder-link.com"))

    def test_external_host_denied(self):
        self.assertFalse(is_host_allowed("evil.example.com"))

    def test_localhost_http_ok(self):
        ok, _ = validate_http_url("http://127.0.0.1:3000/board/wl", purpose="test")
        self.assertTrue(ok)

    def test_external_https_denied(self):
        ok, err = validate_http_url("https://evil.example.com/x", purpose="test")
        self.assertFalse(ok)
        self.assertIn("許可されていない", err)

    def test_update_json_path(self):
        ok, _ = validate_update_check_url(
            "https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/latest.json"
        )
        self.assertTrue(ok)
        ok2, _ = validate_update_check_url("https://evil.example.com/latest.json")
        self.assertFalse(ok2)

    def test_msi_path(self):
        ok, _ = validate_msi_download_url(
            "https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/WonderLinko.msi"
        )
        self.assertTrue(ok)
        ok2, err = validate_msi_download_url("https://wl-ai-board.internal.wonder-link.com/x.exe")
        self.assertFalse(ok2)
        self.assertIn(".msi", err)

    def test_sanitize_reverts_evil_config(self):
        defaults = {
            "mini_port_api_url": "https://wl-ai-board.internal.wonder-link.com/board/wl",
        }
        cfg = {"mini_port_api_url": "https://evil.example.com/steal"}
        sanitize_config_urls(cfg, defaults)
        self.assertEqual(cfg["mini_port_api_url"], defaults["mini_port_api_url"])


if __name__ == "__main__":
    unittest.main()
