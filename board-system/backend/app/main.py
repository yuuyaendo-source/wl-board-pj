# -*- coding: utf-8 -*-
"""
Board System (Wonder Rinko) - FastAPI エントリポイント。
非同期 SQLAlchemy + aiosqlite で SQLite を利用。将来は PostgreSQL へ URL 変更のみで移行可能。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
import app.models  # noqa: F401 — モデルを Base に登録してから create_all するため
from app.routers import board_placements, boards, daily_reset, sticky_notes, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """起動時に DB 初期化（テーブル作成）とパーソナル用ユーザーシード。"""
    await init_db()
    from app.db import seed_personal_users
    await seed_personal_users()
    yield
    # シャットダウン時は特になし（engine はアプリ終了で閉じる）


app = FastAPI(
    title="Board System API (Wonder Rinko)",
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


@app.get("/health")
async def health():
    """死活確認。フロントやロードバランサから利用。"""
    return {"status": "ok", "service": "board-system-backend"}
