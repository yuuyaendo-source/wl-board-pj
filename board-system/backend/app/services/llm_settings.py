# -*- coding: utf-8 -*-
"""
LLM ターゲットの実効解決。DB の system_settings.llm_target があれば優先し、なければ環境変数 LLM_TARGET。
非同期 AsyncSession を使用して安全に検索する。
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)

_SYSTEM_ROW_ID = 1


async def get_db_llm_target_async(db: AsyncSession) -> int | None:
    """DB に保存された LLM スロット上書きを非同期取得。行が無い・NULL なら None。"""
    try:
        result = await db.execute(
            select(SystemSetting.llm_target).where(SystemSetting.id == _SYSTEM_ROW_ID)
        )
        row = result.first()
        if row is None:
            return None
        return row[0]
    except Exception as e:
        logger.warning(
            "[Rinko AI] system_settings 読み取りに失敗（マイグレーション未適用の可能性）: %s",
            e,
        )
        return None


async def get_effective_llm_target_async(db: AsyncSession) -> int | None:
    """実効 LLM スロット: DB 優先、なければ環境変数 LLM_TARGET。"""
    db_t = await get_db_llm_target_async(db)
    if db_t is not None:
        return db_t
    return settings.llm_target


async def get_resolved_ollama_async(db: AsyncSession) -> tuple[str | None, str | None]:
    """
    実効ターゲットに応じた (ollama_base_url, model_override)。
    model_override が None ならクライアント側でモデル自動解決。
    """
    eff = await get_effective_llm_target_async(db)
    return settings.resolve_ollama_for_target(eff)


async def ollama_configured_async(db: AsyncSession) -> bool:
    resolved, _ = await get_resolved_ollama_async(db)
    return bool(resolved)


# --- 互換性・フォールバック用の同期関数 (同期 DB 接続は全廃) ---


def get_db_llm_target_sync() -> int | None:
    """（フォールバック用）DB同期アクセスを廃止したため、環境変数設定を優先。"""
    return None


def get_effective_llm_target_sync() -> int | None:
    """実効 LLM スロット（同期フォールバック）: 環境変数 LLM_TARGET のみ参照。"""
    return settings.llm_target


def get_resolved_ollama_sync() -> tuple[str | None, str | None]:
    """実効ターゲットに応じた (ollama_base_url, model_override)（同期フォールバック）。"""
    eff = get_effective_llm_target_sync()
    return settings.resolve_ollama_for_target(eff)


def ollama_configured_sync() -> bool:
    return bool(get_resolved_ollama_sync()[0])
