# -*- coding: utf-8 -*-
"""
今日の予定（events）をローカル LLM で短縮文にし、Today 用の label を生成する。
"""
from app.ai.client import generate_json


def run_today_short_summaries(
    events: list[dict],
    ollama_url: str | None = None,
    model_override: str | None = None,
) -> list[dict]:
    """
    今日の予定リストを短縮した 1 行ラベルにし、Today 表示用の項目リストを返す。
    events: [{"summary": str, "start": str, "end": str}, ...]
    戻り値: [{"label": str, "summary": str, "start": str, "end": str}, ...]
    LLM 未設定・失敗時は summary をそのまま label に（最大 50 文字）。
    """
    if not events:
        return []
    summaries_for_prompt = [
        f"- {e.get('summary', '') or '(無題)'} ({e.get('start', '')}〜{e.get('end', '')})"
        for e in events
    ]
    prompt = f"""以下の「今日の予定」それぞれを、1行の短い見出し（ラベル）に要約してください。
時刻は含めず、用件だけ短く（例: 14時会議 → 会議、打合せ 10:00 → 打合せ）。

予定一覧:
{chr(10).join(summaries_for_prompt)}

回答は必ず JSON の配列のみにしてください。順番は予定一覧と同じにし、各要素は短いラベル文字列1つにしてください。
["ラベル1", "ラベル2", ...]
"""
    data = generate_json(prompt, ollama_url=ollama_url, model_override=model_override)
    labels = []
    if isinstance(data, list) and len(data) >= len(events):
        labels = [str(x).strip()[:80] if x else "" for x in data[: len(events)]]
    elif isinstance(data, list):
        labels = [str(x).strip()[:80] if x else "" for x in data]
        while len(labels) < len(events):
            labels.append("")
    if not labels or len(labels) != len(events):
        labels = [((e.get("summary") or "")[:50] or "(無題)") for e in events]
    out = []
    for e, label in zip(events, labels):
        out.append(
            {
                "label": label or (e.get("summary") or "")[:50] or "(無題)",
                "summary": e.get("summary", ""),
                "start": e.get("start", ""),
                "end": e.get("end", ""),
            }
        )
    return out
