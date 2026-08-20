"""呼ばれ方編集クライアント（get_self_profile / update_self_profile）のテスト。

HTTP レイヤ（_request）はモックし、正しいメソッド・パス・ボディ・トークンで
linko の /self_register/profile を叩くことを確認する。
"""

import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import face_registry_self_client as c


class TestSelfProfileClient(unittest.TestCase):
    def test_get_uses_get_with_person_id_and_token(self):
        with mock.patch.object(
            c, "_request", return_value={"call_name": "浅川", "honorific": "さん"}
        ) as req:
            out = c.get_self_profile({"linko_server_url": "http://x"}, "42", "tok")
        self.assertEqual(out["call_name"], "浅川")
        args, kwargs = req.call_args
        self.assertEqual(args[1], "GET")
        self.assertEqual(args[2], "/self_register/profile")
        self.assertEqual(kwargs.get("token"), "tok")
        self.assertEqual(kwargs.get("params"), {"person_id": "42"})

    def test_update_sends_only_provided_fields(self):
        with mock.patch.object(c, "_request", return_value={}) as req:
            c.update_self_profile(
                {"linko_server_url": "http://x"},
                "42",
                "tok",
                call_name="浅やん",
                honorific="",
            )
        args, kwargs = req.call_args
        self.assertEqual(args[1], "POST")
        self.assertEqual(args[2], "/self_register/profile")
        body = kwargs.get("json_body")
        self.assertEqual(body.get("person_id"), "42")
        self.assertEqual(body.get("call_name"), "浅やん")
        self.assertEqual(body.get("honorific"), "")  # 空文字＝敬称なしも送る
        self.assertNotIn("call_name_kana", body)  # 未指定は送らない
        self.assertEqual(kwargs.get("token"), "tok")

    def test_update_can_send_empty_honorific(self):
        """★空文字の敬称（敬称なし）を明示的に送れること。"""
        with mock.patch.object(c, "_request", return_value={}) as req:
            c.update_self_profile(
                {"linko_server_url": "http://x"}, "42", "tok", honorific=""
            )
        body = req.call_args.kwargs.get("json_body")
        self.assertIn("honorific", body)
        self.assertEqual(body["honorific"], "")


if __name__ == "__main__":
    unittest.main()
