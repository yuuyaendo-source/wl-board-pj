# -*- coding: utf-8 -*-
"""
Logic 2: Matrix Scoring（マトリクス配置）。
Task Board に載せるタスクの緊急度・重要度を 0-100 で採点する。
"""
from app.ai.client import generate_json


def _quadrant_from_xy(x: float, y: float) -> int:
    """
    アイゼンハワー: x=緊急度, y=重要度 のとき
    象限 1: 緊急かつ重要, 2: 重要だが非緊急, 3: 緊急だが非重要, 4: どちらでもない
    一般的に x=緊急度(横), y=重要度(縦) で、右上が1、左上が2、右下が3、左下が4。
    0-100 で 50 を境界とする。
    """
    if x >= 50 and y >= 50:
        return 1
    if x < 50 and y >= 50:
        return 2
    if x >= 50 and y < 50:
        return 3
    return 4


def run_matrix_scoring(content: str) -> dict | None:
    """
    付箋本文から緊急度・重要度を 0-100 で取得する。
    戻り値: None or {"urgency": 0-100, "importance": 0-100}
    position_x = urgency, position_y = importance で保存し、
    matrix_quadrant は _quadrant_from_xy(urgency, importance) で算出する。
    """
    prompt = f"""以下のタスクについて、「緊急度」と「重要度」をそれぞれ 0 以上 100 以下の整数で採点してください。

タスク:「{content[:500]}」

- 緊急度: 期限が近い・すぐ対応すべきほど高い。
- 重要度: 成果・影響が大きいほど高い。

回答は必ず次の JSON 形式のみにしてください。
{{"urgency": 0以上100以下の整数, "importance": 0以上100以下の整数}}
"""
    data = generate_json(prompt)
    if not data:
        return None
    try:
        u = int(data.get("urgency", 50))
        i = int(data.get("importance", 50))
        u = max(0, min(100, u))
        i = max(0, min(100, i))
    except (TypeError, ValueError):
        u, i = 50, 50
    return {
        "urgency": u,
        "importance": i,
        "matrix_quadrant": _quadrant_from_xy(float(u), float(i)),
    }
