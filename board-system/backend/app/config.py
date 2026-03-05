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

    # ローカル LLM（Ollama）。未設定なら自動仕分け・スコアリングはスキップ
    ollama_url: str | None = None

    @field_validator("ollama_url")
    @classmethod
    def strip_ollama_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = (v or "").strip().rstrip("/")
        return v if v else None

    ollama_model: str = "llama3.2"

    # Gemini API（未使用: ローカル LLM 利用のためコメントアウト）
    # gemini_api_key: str | None = None
    # @field_validator("gemini_api_key")
    # @classmethod
    # def strip_api_key(cls, v: str | None) -> str | None:
    #     if v is None:
    #         return None
    #     v = (v or "").strip()
    #     return v if v else None
    # gemini_model: str = "gemini-2.0-flash"

    # 付箋ボード（02_1）のベースURL。タスクゴミ箱からは削除せず PATCH でグレー化する
    postit_board_url: str = "http://127.0.0.1:3000"
    # 付箋ボードのボードID（Board System でタスクになった付箋をここに反映する）
    postit_board_id: str = "wl"

    # Google カレンダー連携（OAuth 2.0）。未設定ならカレンダー連携は無効
    google_calendar_client_id: str | None = None
    google_calendar_client_secret: str | None = None
    google_calendar_redirect_uri: str | None = None  # 例: https://wl-ai-board.example.com/auth/google/callback
    # カレンダー「今日」のタイムゾーン。その日 0:00〜23:59 の取得に使用（例: Asia/Tokyo）
    calendar_timezone: str = "Asia/Tokyo"

    # OAuth 成功後のリダイレクト先のプレフィックス。本番で Next basePath が /boards のときは "/boards" を指定
    oauth_success_redirect_base: str = ""

    # 日次スケジュール（日本時間 8:00 run_8am / 10:15 sync_to_morning）。無効にする場合は false
    scheduler_enabled: bool = True
    # スケジューラが POST する自サーバの URL（同一プロセス内で HTTP 呼び出しするため）。例: http://127.0.0.1:8000
    scheduler_base_url: str = "http://127.0.0.1:8000"

    @field_validator("scheduler_base_url")
    @classmethod
    def strip_scheduler_base_url(cls, v: str | None) -> str:
        if v is None:
            return "http://127.0.0.1:8000"
        return (v or "").strip().rstrip("/")

    @field_validator("oauth_success_redirect_base")
    @classmethod
    def strip_oauth_success_base(cls, v: str | None) -> str:
        if v is None:
            return ""
        return (v or "").strip().rstrip("/")

    @field_validator("google_calendar_redirect_uri")
    @classmethod
    def strip_redirect_uri(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = (v or "").strip().rstrip("/")
        return v if v else None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
