# -*- coding: utf-8 -*-
"""改善計画18: スタートアップ設定・自動同期のテスト。"""
import os
import sys
import unittest

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config_loader
import startup
import app


class TestStartupAndConfig(unittest.TestCase):
    def test_default_startup_enabled(self):
        defaults = config_loader._get_defaults()
        self.assertIn("startup_enabled", defaults)
        self.assertTrue(defaults["startup_enabled"])

    def test_startup_methods(self):
        # メソッドが例外なく動作し、bool を返すことを検証
        is_disabled = startup.is_disabled_by_task_manager()
        self.assertIsInstance(is_disabled, bool)

        is_enabled = startup.is_startup_enabled()
        self.assertIsInstance(is_enabled, bool)

    def test_sync_startup_setting_runs(self):
        # 例外なく実行されることを検証
        app._sync_startup_setting()


if __name__ == "__main__":
    unittest.main()
