# -*- coding: utf-8 -*-
"""settings_dialog の構造・メソッド定義のユニットテスト。"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import settings_dialog


class TestSettingsDialogStructure(unittest.TestCase):
    def test_methods_exist(self):
        self.assertTrue(hasattr(settings_dialog.SettingsDialog, "_save_settings"))
        self.assertTrue(hasattr(settings_dialog.SettingsDialog, "_bind_entry"))
        self.assertTrue(hasattr(settings_dialog.SettingsDialog, "_on_close"))
        self.assertTrue(hasattr(settings_dialog.SettingsDialog, "_on_update_clicked"))


if __name__ == "__main__":
    unittest.main()
