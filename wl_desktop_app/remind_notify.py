# -*- coding: utf-8 -*-
"""タスク/カレンダーリマインドのトースト・吹き出し・音声を統一配信。"""
from __future__ import annotations

TASK_VOICE_TEXT = "お疲れ様です。本日の進捗はいかがですか？"


def deliver_remind(
    toast_title: str,
    toast_message: str,
    bubble_text: str,
    *,
    voice_text: str | None = None,
    duration_sec: int = 10,
) -> None:
    """notifications_enabled 準拠。remind_voice ON なら TTS、でなければ linko_avatar で吹き出しのみ。"""
    try:
        from notifications import are_enabled, show_toast
        if not are_enabled():
            return
        show_toast(toast_title, toast_message, duration_sec=duration_sec)
    except Exception:
        pass

    try:
        from config_loader import is_feature_enabled
        if is_feature_enabled("remind_voice") and voice_text:
            from audio_player import speak_text
            speak_text(voice_text)
            return
        if is_feature_enabled("linko_avatar") and bubble_text:
            import linko_avatar
            linko_avatar.say(bubble_text, duration_sec=duration_sec, lipsync=False)
    except Exception:
        pass
