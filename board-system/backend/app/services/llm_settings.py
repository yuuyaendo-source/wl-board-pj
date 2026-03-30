# -*- coding: utf-8 -*-
"""
LLM ターゲットの実効解決。DB の system_settings.llm_target があれば優先し、なければ環境変数 LLM_TARGET。
同期 DB で読む（Ollama クライアントが sync のため）。orchestrator の担当者解決と同様に psycopg2/sqlite を利用。
"""
from __future__ import annotations

import logging

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_ROW_ID = 1


def _sync_database_url() -> str:
    url = settings.database_url
    if "postgresql+asyncpg" in url:
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)
    if "sqlite+aiosqlite" in url:
        return url.replace("sqlite+aiosqlite", "sqlite", 1)
    return url


def get_db_llm_target_sync() -> int | None:
    """DB に保存された LLM スロット上書き。行が無い・NULL なら None。"""
    from app.models.system_setting import SystemSetting

    url = _sync_database_url()
    engine = create_engine(url)
    try:
        with Session(engine) as session:
            row = session.execute(
                select(SystemSetting.llm_target).where(SystemSetting.id == _SYSTEM_ROW_ID)
            ).first()
            if row is None:
                return None
            return row[0]
    except Exception as e:
        logger.warning("[Rinko AI] system_settings 読み取りに失敗（マイグレーション未適用の可能性）: %s", e)
        return None


def get_effective_llm_target_sync() -> int | None:
    """実効 LLM スロット: DB 優先、なければ環境変数 LLM_TARGET。"""
    db_t = get_db_llm_target_sync()
    if db_t is not None:
        return db_t
    return settings.llm_target


def get_resolved_ollama_sync() -> tuple[str | None, str | None]:
    """
    実効ターゲットに応じた (ollama_base_url, model_override)。
    model_override が None ならクライアント側でモデル自動解決。
    """
    eff = get_effective_llm_target_sync()
    return settings.resolve_ollama_for_target(eff)


def ollama_configured_sync() -> bool:
    return bool(get_resolved_ollama_sync()[0])
