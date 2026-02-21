# -*- coding: utf-8 -*-
"""
Logic 1: Auto-Triage（自動仕分け）。
Main Board 新規投稿が「タスクか情報か」「担当者明記か」を LLM で判定し、結果を返す。
"""
from app.ai.client import generate_json


def run_triage(content: str) -> dict | None:
    """
    付箋本文からタスク判定と担当者名を取得する。
    戻り値: None（API 未設定・失敗） or
           {"is_task": bool, "assignee_name": str | None}
    担当者名は users.name で検索する想定（部分一致で可）。
    """
    prompt = f"""以下の投稿を分析し、JSON のみで答えてください。

投稿:「{content[:500]}」

質問:
1. この投稿は「タスク（作業・やるべきこと）」ですか？ それとも「情報の共有・雑談」ですか？
2. タスクの場合、特定の担当者（人名）が明記されていますか？ いる場合は「苗字」または「苗字 名前」で抽出し、敬称（さん・君・様など）は付けないでください。例: 浅川さん→浅川、田中様お願い→田中。
3. 上記1の判定理由を1行で端的に（例: 期限付きの作業依頼のため / 共有メモのため）。

回答は必ず次の JSON 形式のみにしてください。他に説明は不要です。
{{"is_task": true または false, "assignee_name": "担当者名（敬称なし。いなければ null）", "reason": "判定理由を1行で"}}
"""
    data = generate_json(prompt)
    if not data:
        return None
    # LLM が "true" を文字列で返す場合にも対応（is True のみだと False になる）
    raw_is_task = data.get("is_task")
    is_task = raw_is_task is True or (isinstance(raw_is_task, str) and raw_is_task.strip().lower() == "true")
    assignee = data.get("assignee_name")
    if isinstance(assignee, str):
        assignee = assignee.strip() or None
    else:
        assignee = None
    reason = data.get("reason")
    if isinstance(reason, str):
        reason = reason.strip() or None
    else:
        reason = None
    return {"is_task": is_task, "assignee_name": assignee, "reason": reason}
