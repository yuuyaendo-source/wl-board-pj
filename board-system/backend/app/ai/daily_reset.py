# -*- coding: utf-8 -*-
"""
Logic 3: Daily Reset（日次リセット）。
Personal Board の Today にある未完了タスクについて、
「昨日の『〇〇』は持ち越しますか？」形式の問いかけメッセージを生成する。
"""
from app.ai.client import generate_json


def run_daily_reset_messages(
    items: list[dict],
) -> list[str]:
    """
    items: [{"note_id": int, "content": str}, ...]（Today レーンの付箋一覧）
    戻り値: 各付箋に対する「持ち越しますか？」メッセージのリスト。
    API 未設定・失敗時は簡易メッセージを返す。
    """
    if not items:
        return []
    contents = [x.get("content", "")[:100] for x in items]
    prompt = f"""以下の「今日やると決めたタスク」について、ユーザーへの問いかけ文を1文ずつ生成してください。
各タスクに対して「昨日の『〇〇』は持ち越しますか？」のように、タスク内容を引用した一文にしてください。

タスク一覧:
{chr(10).join(f"- {c}" for c in contents)}

回答は必ず JSON の配列のみにしてください。順番はタスク一覧と同じにしてください。
["昨日の『タスク1』は持ち越しますか？", "昨日の『タスク2』は持ち越しますか？", ...]
"""
    data = generate_json(prompt)
    if isinstance(data, list) and len(data) >= len(items):
        return [str(m) for m in data[: len(items)]]
    if isinstance(data, list):
        return [str(m) for m in data]
    # フォールバック: 簡易メッセージ
    return [f"「{x.get('content', '')[:30]}」は持ち越しますか？" for x in items]
