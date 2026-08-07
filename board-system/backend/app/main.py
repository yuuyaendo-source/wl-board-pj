# -*- coding: utf-8 -*-
"""
Board System (Wonder Linko) - FastAPI エントリポイント。
非同期 SQLAlchemy + aiosqlite で SQLite を利用。将来は PostgreSQL へ URL 変更のみで移行可能。
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_db
import app.models  # noqa: F401 — モデルを Base に登録してから create_all するため
from app.routers import (
    admin_llm,
    auth_google,
    board_placements,
    boards,
    brainstorm,
    daily_reset,
    news,
    personal,
    sticky_notes,
    task_reminders,
    calendar_reminders,
    teams,
    users,
)

logger = logging.getLogger(__name__)

# デスクトップアプリ自動更新用リリース置き場（backend/desktop_app_releases）
_DESKTOP_APP_RELEASES_DIR = Path(__file__).resolve().parent.parent / "desktop_app_releases"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時に DB 初期化（テーブル作成）とパーソナル用ユーザーシード。"""
    await init_db()
    from app.db import seed_personal_users, seed_teams
    await seed_personal_users()
    await seed_teams()
    from app.services.llm_settings import get_effective_llm_target_sync, get_resolved_ollama_sync

    url, model_ov = get_resolved_ollama_sync()
    if url:
        eff = get_effective_llm_target_sync()
        tgt = f" [effective_LLM_TARGET={eff}]" if eff is not None else ""
        model_line = model_ov or "自動（Ollama のローカルモデル一覧から解決）"
        logger.info(
            "[Rinko AI] OLLAMA 設定済み — 自動振り分け・スコアリングが有効です (model=%s)%s",
            model_line,
            tgt,
        )
    else:
        logger.warning("[Rinko AI] OLLAMA_URL 未設定 — 自動振り分けはスキップされ、付箋はすべてアイデア列に入ります")
    try:
        from app.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        logger.warning("スケジューラ起動をスキップ: %s", e)
    yield
    try:
        from app.scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="Board System API (Wonder Linko)",
    description="4ボード（Main / Task / Personal / Morning）用のバックエンドAPI。",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(teams.router)
app.include_router(sticky_notes.router)
app.include_router(board_placements.router)
app.include_router(boards.router)
app.include_router(daily_reset.router)
app.include_router(news.router)
app.include_router(personal.router)
app.include_router(task_reminders.router)
app.include_router(calendar_reminders.router)
app.include_router(auth_google.router)
app.include_router(admin_llm.router)
app.include_router(brainstorm.router)

# デスクトップアプリ自動更新: /desktop-app/latest.json と /desktop-app/WonderLinko.msi を配信
if _DESKTOP_APP_RELEASES_DIR.is_dir():
    app.mount("/desktop-app", StaticFiles(directory=str(_DESKTOP_APP_RELEASES_DIR)), name="desktop_app_releases")


@app.get("/health")
async def health():
    """死活確認。フロントやロードバランサから利用。"""
    return {"status": "ok", "service": "board-system-backend"}
