# -*- coding: utf-8 -*-
"""
Board System (Wonder Linko) - FastAPI エントリポイント。
非同期 SQLAlchemy + aiosqlite で SQLite を利用。将来は PostgreSQL へ URL 変更のみで移行可能。
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
import app.models  # noqa: F401 — モデルを Base に登録してから create_all するため
from app.routers import auth_google, board_placements, boards, daily_reset, personal, sticky_notes, users

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時に DB 初期化（テーブル作成）とパーソナル用ユーザーシード。"""
    await init_db()
    from app.db import seed_personal_users
    await seed_personal_users()
    if settings.ollama_url:
        logger.info("[Rinko AI] OLLAMA_URL 設定済み — 自動振り分け・スコアリングが有効です (model=%s)", settings.ollama_model)
    else:
        logger.warning("[Rinko AI] OLLAMA_URL 未設定 — 自動振り分けはスキップされ、付箋はすべてアイデア列に入ります")
    yield
    # シャットダウン時は特になし（engine はアプリ終了で閉じる）


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
app.include_router(sticky_notes.router)
app.include_router(board_placements.router)
app.include_router(boards.router)
app.include_router(daily_reset.router)
app.include_router(personal.router)
app.include_router(auth_google.router)


@app.get("/health")
async def health():
    """死活確認。フロントやロードバランサから利用。"""
    return {"status": "ok", "service": "board-system-backend"}
