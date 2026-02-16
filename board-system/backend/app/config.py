# -*- coding: utf-8 -*-
"""
設定。環境変数から読み込み（.env 対応）。
将来的に PostgreSQL へ切り替える場合は DATABASE_URL を変更するだけにする。
"""
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリ設定。環境変数で上書き可能。"""

    # DB: SQLite (開発) は sqlite+aiosqlite。本番は postgresql+asyncpg 等に変更
    database_url: str = "sqlite+aiosqlite:///./board.db"

    # Gemini API（フェーズ3 AI Worker）。未設定なら自動仕分け・スコアリングはスキップ
    gemini_api_key: str | None = None

    @field_validator("gemini_api_key")
    @classmethod
    def strip_api_key(cls, v: str | None) -> str | None:
        """ .env の改行・余白を除去 """
        if v is None:
            return None
        v = (v or "").strip()
        return v if v else None
    gemini_model: str = "gemini-2.0-flash"

    # 付箋ボード（02_1）のベースURL。タスクゴミ箱からは削除せず PATCH でグレー化する
    postit_board_url: str = "http://127.0.0.1:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
