"""開錠失敗（なりすまし疑い）のセキュリティ警報テスト。

背景（2026-07-15 実機）:
  写真/動画のなりすましを anti-spoof が弾き、対応パネルへエスカレーションしたが、
  デスクトップアプリが**音を鳴らさなかった**。原因は音再生が opt-in 設定
  (visitor_notify_sound・既定 False) と TTS(audio_url) の両方に依存していたため。

対策:
  action == "unlock_failed" は**セキュリティ警報**として、opt-in 設定にも TTS 成否にも
  依存せず必ず警報音を鳴らす（通常の来客通知は従来どおり opt-in のまま）。
"""

import os
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import visitor_notify_client as vnc  # noqa: E402


def _install_fake_deps():
    """_handle_visitor_arrived が関数内で import する依存をフェイクに差し替える。"""
    fakes = {}

    notifications = types.ModuleType("notifications")
    notifications.are_enabled = lambda: True
    notifications.show_toast = lambda *a, **k: None
    fakes["notifications"] = notifications

    config_loader = types.ModuleType("config_loader")
    config_loader.load_config = lambda: {"linko_server_url": "http://x"}
    # 通常来客の音は既定 OFF（opt-in）。セキュリティ警報がこれに依存しないことを確かめる。
    config_loader.is_feature_enabled = lambda name, cfg=None: False
    fakes["config_loader"] = config_loader

    security = types.ModuleType("security")
    security.filter_allowed_url = lambda url, cfg, purpose=None: url
    fakes["security"] = security

    return fakes


class TestSecurityAlert(unittest.TestCase):
    def setUp(self):
        self._saved = {
            k: sys.modules.get(k)
            for k in ("notifications", "config_loader", "security")
        }
        sys.modules.update(_install_fake_deps())

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v

    def test_unlock_failed_plays_guaranteed_alert(self):
        """★開錠失敗は、音設定 OFF・TTS 無しでも必ず警報音を鳴らす。"""
        with mock.patch.object(vnc, "_play_security_alert") as alert, mock.patch.object(
            vnc, "_play_visitor_audio"
        ) as tts:
            vnc._handle_visitor_arrived(
                {
                    "name": "浅川",
                    "location": "entrance",
                    "action": "unlock_failed",
                    "audio_url": "",  # TTS 無し
                }
            )
            alert.assert_called_once()  # 警報は必ず鳴る
            tts.assert_not_called()  # TTS が無いので読み上げは無い（警報だけ）

    def test_unlock_failed_overlays_tts_when_present(self):
        """TTS 音声があれば警報音のあとに重ねて読み上げる。"""
        with mock.patch.object(vnc, "_play_security_alert") as alert, mock.patch.object(
            vnc, "_play_visitor_audio"
        ) as tts:
            vnc._handle_visitor_arrived(
                {
                    "name": "浅川",
                    "location": "entrance",
                    "action": "unlock_failed",
                    "audio_url": "/static/voices/x.wav",
                }
            )
            alert.assert_called_once()
            tts.assert_called_once()

    def test_normal_visitor_stays_opt_in(self):
        """★通常の来客通知は従来どおり: 音設定 OFF なら鳴らさない（うるさくしない）。"""
        with mock.patch.object(vnc, "_play_security_alert") as alert, mock.patch.object(
            vnc, "_play_visitor_audio"
        ) as tts:
            vnc._handle_visitor_arrived(
                {
                    "name": "坂井",
                    "location": "entrance",
                    "action": "call_human",
                    "audio_url": "/static/voices/y.wav",
                }
            )
            alert.assert_not_called()  # セキュリティ警報ではない
            tts.assert_not_called()  # visitor_notify_sound=False なので鳴らさない


class TestBeep(unittest.TestCase):
    def test_security_alert_beeps_via_winsound(self):
        """_play_security_alert は winsound.Beep を鳴らす（TTS 非依存の確実な音）。"""
        fake_winsound = types.ModuleType("winsound")
        fake_winsound.Beep = mock.MagicMock()
        saved = sys.modules.get("winsound")
        sys.modules["winsound"] = fake_winsound
        try:
            threads_before = None
            vnc._play_security_alert()
            # バックグラウンドスレッドで鳴らすので、少し待って join する。
            import threading

            for t in threading.enumerate():
                if t is not threading.current_thread() and t.daemon:
                    t.join(timeout=2.0)
            self.assertTrue(
                fake_winsound.Beep.called, "警報は winsound.Beep を呼ぶこと"
            )
        finally:
            if saved is None:
                sys.modules.pop("winsound", None)
            else:
                sys.modules["winsound"] = saved


if __name__ == "__main__":
    unittest.main()
