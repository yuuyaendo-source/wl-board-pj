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
    """notifications_enabled 準拠。remind_voice ON なら TTS、でなければ show_toast で吹き出し通知。"""
    try:
        from services.notifications import are_enabled, show_toast
        from core.config_loader import is_feature_enabled

        if not are_enabled():
            return

        # 音声リマインド有効時は TTS 音声再生を実行（内部でアバター吹き出し・口パクと同期）
        if is_feature_enabled("remind_voice") and voice_text:
            from hardware.audio_player import speak_text

            speak_text(voice_text)
            return

        # 音声無効時は show_toast 経由でタイトル付き吹き出しを1回のみ表示
        # （改善計画25で show_toast 自体がアバター吹き出しに一本化されているため、二重実行を防ぐ）
        show_toast(toast_title, toast_message, duration_sec=duration_sec)
    except Exception:
        pass
