# -*- coding: utf-8 -*-
"""
設定。環境変数から読み込み（.env 対応）。
将来的に PostgreSQL へ切り替える場合は DATABASE_URL を変更するだけにする。
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリ設定。環境変数で上書き可能。"""

    # DB: SQLite (開発) は sqlite+aiosqlite。本番は postgresql+asyncpg 等に変更
    database_url: str = "sqlite+aiosqlite:///./board.db"

    # Gemini API（フェーズ3 AI Worker）。未設定なら自動仕分け・スコアリングはスキップ
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash-lite"

    # 付箋ボード（02_1）のベースURL。タスクゴミ箱から削除時に 02_1 へ DELETE 連携する
    postit_board_url: str = "http://127.0.0.1:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
