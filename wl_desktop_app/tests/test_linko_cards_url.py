# -*- coding: utf-8 -*-
"""リン子カード深いリンクの単体テスト。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from linko_cards import build_linko_cards_url


class TestLinkoCardsUrl(unittest.TestCase):
    def test_prefers_board_system_email(self):
        url = build_linko_cards_url(
            {
                "linko_server_url": "https://linko-board.internal.wonder-link.com",
                "board_system_email": "asakawa@example.com",
                "face_registry_person_id": "浅川久司",
                "display_name": "浅川",
            }
        )
        self.assertEqual(
            url,
            "https://linko-board.internal.wonder-link.com/entrance/me/cards"
            "?email=asakawa%40example.com",
        )

    def test_falls_back_to_face_registry_person_id(self):
        url = build_linko_cards_url(
            {
                "linko_server_url": "https://linko-board.internal.wonder-link.com",
                "board_system_email": "",
                "face_registry_person_id": "浅川久司",
                "display_name": "浅川",
            }
        )
        self.assertTrue(
            url.startswith(
                "https://linko-board.internal.wonder-link.com/entrance/me/cards?"
            )
        )
        self.assertIn("employee_id=", url)

    def test_falls_back_to_display_name(self):
        url = build_linko_cards_url(
            {
                "linko_server_url": "http://127.0.0.1:5000",
                "board_system_email": "",
                "face_registry_person_id": "",
                "display_name": "小林",
            }
        )
        self.assertEqual(
            url,
            "http://127.0.0.1:5000/entrance/me/cards?employee_id=%E5%B0%8F%E6%9E%97",
        )


if __name__ == "__main__":
    unittest.main()
