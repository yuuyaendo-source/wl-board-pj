# -*- coding: utf-8 -*-
"""
設定。環境変数から読み込み（.env 対応）。
将来的に PostgreSQL へ切り替える場合は DATABASE_URL を変更するだけにする。
"""
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリ設定。環境変数で上書き可能。"""

    # DB: SQLite (開発) は sqlite+aiosqlite。本番は postgresql+asyncpg 等に変更
    database_url: str = "sqlite+aiosqlite:///./board.db"

    # 社内 LLM Docker を複数台切り替え: 1〜3 を指定すると OLLAMA_URL_n / OLLAMA_MODEL_n を採用。
    # 未設定なら従来どおり OLLAMA_URL / OLLAMA_MODEL のみ。
    llm_target: int | None = Field(default=None, ge=1, le=3)

    # ローカル LLM（Ollama）。未設定なら自動仕分け・スコアリングはスキップ
    ollama_url: str | None = None
    ollama_url_1: str | None = None
    ollama_url_2: str | None = None
    ollama_url_3: str | None = None

    @field_validator(
        "ollama_url",
        "ollama_url_1",
        "ollama_url_2",
        "ollama_url_3",
        mode="before",
    )
    @classmethod
    def strip_optional_ollama_urls(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = (v or "").strip().rstrip("/")
        return v if v else None

    # 未設定・空なら Ollama から自動解決（/api/tags の最新 modified_at 優先）。指定時は固定モデル
    ollama_model: str | None = None
    ollama_model_1: str | None = None
    ollama_model_2: str | None = None
    ollama_model_3: str | None = None
    # 自動解決したモデル名のキャッシュ秒数（同一エンドポイントへの連続呼び出し抑制）
    ollama_model_auto_cache_ttl_seconds: int = 600

    @field_validator("ollama_model", mode="before")
    @classmethod
    def ollama_model_empty_to_none(cls, v: object) -> str | None:
        if v is None or v == "":
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("llm_target", mode="before")
    @classmethod
    def llm_target_empty_to_none(cls, v: object) -> int | None:
        if v is None or v == "":
            return None
        return int(v)

    @field_validator("ollama_model_1", "ollama_model_2", "ollama_model_3", mode="before")
    @classmethod
    def optional_model_strip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

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

    # 日次スケジュール（日本時間 8:00 run_8am / 10:00 clear_news / 10:15 sync_to_morning + fetch_news）。無効にする場合は false
    scheduler_enabled: bool = True
    # テスト用: ニュース取得を N 分ごとに実行（0 または未設定で無効）。例: 3 で 3 分ごと
    scheduler_news_interval_minutes: int = 0
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

    @model_validator(mode="after")
    def resolve_llm_target(self) -> "Settings":
        """LLM_TARGET 指定時は対応する URL/モデルへ集約（各 Docker のデフォルトを分けて保持可能）。"""
        t = self.llm_target
        if t is None:
            return self
        urls = {1: self.ollama_url_1, 2: self.ollama_url_2, 3: self.ollama_url_3}
        models = {1: self.ollama_model_1, 2: self.ollama_model_2, 3: self.ollama_model_3}
        chosen_url = urls[t] or self.ollama_url
        chosen_model = models[t] or self.ollama_model
        if not chosen_url:
            raise ValueError(
                f"LLM_TARGET={t} のときは OLLAMA_URL_{t} か、フォールバック用の OLLAMA_URL を設定してください。"
            )
        return self.model_copy(update={"ollama_url": chosen_url, "ollama_model": chosen_model})

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
