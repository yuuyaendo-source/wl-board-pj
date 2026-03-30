# -*- coding: utf-8 -*-
"""管理用: LLM エンドポイント（スロット）の切替。DB で環境変数 LLM_TARGET を上書き。"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import invalidate_resolved_model_cache
from app.config import settings
from app.db import get_db
from app.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/llm", tags=["admin"])


class LlmStatusResponse(BaseModel):
    db_llm_target: int | None = Field(description="DB に保存した上書き。null は DB 未設定で env に従う")
    env_llm_target: int | None
    effective_llm_target: int | None
    resolved_url: str | None
    model_override: str | None = Field(description="環境で固定モデル指定時のみ。null なら自動解決")
    model_mode: str = Field(description='"auto" | "fixed"')


class LlmUpdateBody(BaseModel):
    """llm_target: 1〜3 で DB に保存して即反映。null で DB 上書きを解除し環境変数 LLM_TARGET に従う。"""

    llm_target: int | None = Field(..., description="1〜3、または null")

    @field_validator("llm_target")
    @classmethod
    def check_slot(cls, v: int | None) -> int | None:
        if v is None:
            return None
        if v not in (1, 2, 3):
            raise ValueError("llm_target は 1〜3 または null である必要があります")
        return v


@router.get("", response_model=LlmStatusResponse)
async def get_llm_status(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SystemSetting).where(SystemSetting.id == 1))
    row = result.scalar_one_or_none()
    db_t = row.llm_target if row else None
    eff = db_t if db_t is not None else settings.llm_target
    url, model_ov = settings.resolve_ollama_for_target(eff)
    return LlmStatusResponse(
        db_llm_target=db_t,
        env_llm_target=settings.llm_target,
        effective_llm_target=eff,
        resolved_url=url,
        model_override=model_ov,
        model_mode="fixed" if model_ov else "auto",
    )


@router.put("", response_model=LlmStatusResponse)
async def put_llm_status(body: LlmUpdateBody, db: AsyncSession = Depends(get_db)):
    if body.llm_target is not None:
        url, _ = settings.resolve_ollama_for_target(body.llm_target)
        if not url:
            raise HTTPException(
                status_code=400,
                detail=f"LLM_TARGET={body.llm_target} に対応する URL が未設定です（OLLAMA_URL_{body.llm_target} または OLLAMA_URL）",
            )

    result = await db.execute(select(SystemSetting).where(SystemSetting.id == 1))
    row = result.scalar_one_or_none()
    if row is None:
        row = SystemSetting(id=1, llm_target=body.llm_target)
        db.add(row)
    else:
        row.llm_target = body.llm_target

    await db.flush()
    invalidate_resolved_model_cache(None)
    logger.info("[Rinko AI] admin: llm_target を更新 db=%s", body.llm_target)

    eff = body.llm_target if body.llm_target is not None else settings.llm_target
    url, model_ov = settings.resolve_ollama_for_target(eff)
    return LlmStatusResponse(
        db_llm_target=body.llm_target,
        env_llm_target=settings.llm_target,
        effective_llm_target=eff,
        resolved_url=url,
        model_override=model_ov,
        model_mode="fixed" if model_ov else "auto",
    )
