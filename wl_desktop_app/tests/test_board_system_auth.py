# -*- coding: utf-8 -*-
"""services/board_system_auth.py の単体テスト。"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.board_system_auth import (
    BoardSystemAuthError,
    resolve_user_by_email,
    login_with_email,
)


class TestBoardSystemAuth(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "board_system_url": "https://example.com/board/wl",
        }

    def test_resolve_empty_email(self):
        with self.assertRaises(BoardSystemAuthError):
            resolve_user_by_email("", self.cfg)

    def test_resolve_invalid_email(self):
        with self.assertRaises(BoardSystemAuthError):
            resolve_user_by_email("invalid-email", self.cfg)

    @patch("services.board_system_auth.requests.get")
    def test_resolve_user_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "email": "user@example.com",
            "name": "Test User",
        }
        mock_get.return_value = mock_response

        data = resolve_user_by_email("user@example.com", self.cfg)
        self.assertEqual(data["id"], 123)
        self.assertEqual(data["email"], "user@example.com")

    @patch("services.board_system_auth.requests.get")
    @patch("services.board_system_auth.save_board_system_login")
    def test_login_with_email_success(self, mock_save, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 42,
            "email": "taro@example.com",
            "name": "Taro Yamada",
        }
        mock_get.return_value = mock_response

        success, msg, personal_url = login_with_email("taro@example.com", self.cfg)
        self.assertTrue(success)
        self.assertIn("ログインしました", msg)
        mock_save.assert_called_once()


if __name__ == "__main__":
    unittest.main()