# -*- coding: utf-8 -*-
"""
Rinko Core: ローカル LLM（Ollama）を用いた自動仕分け・マトリクススコア・日次リセット。
OLLAMA_URL 未設定時は各関数は None または空を返し、呼び出し元でスキップする。
"""
from app.ai.triage import run_triage
from app.ai.matrix import run_matrix_scoring
from app.ai.daily_reset import run_daily_reset_messages
from app.ai.today_summary import run_today_short_summaries

__all__ = ["run_triage", "run_matrix_scoring", "run_daily_reset_messages", "run_today_short_summaries"]
