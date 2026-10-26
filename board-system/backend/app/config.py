# -*- coding: utf-8 -*-
"""
設定。環境変数から読み込み（.env 対応）。
将来的に PostgreSQL へ切り替える場合は DATABASE_URL を変更するだけにする。
"""
import logging
import hashlib
import os
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """アプリ設定。環境変数で上書き可能。"""

    # DB: SQLite (開発) は sqlite+aiosqlite。本番は postgresql+asyncpg 等に変更
    database_url: str = "sqlite+aiosqlite:///./board.db"

    # CORS 許可オリジン（カンマ区切り）
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:3010,http://127.0.0.1:3010,https://wlboardsys.internal.wonder-link.com"
    )

    # 内部通信用共有シークレット（付箋ボード・内部API間認証）
    internal_api_secret: str = Field(default="wl-internal-secret-change-in-production")

    # 管理者用パスワードと JWT 設定
    admin_password: str = Field(default="admin123")
    jwt_secret: str = Field(default="super-secret-key-change-in-production-12345")
    jwt_expire_minutes: int = 1440  # 24時間
    environment: str = Field(default="development")

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

    @field_validator(
        "ollama_model_1", "ollama_model_2", "ollama_model_3", mode="before"
    )
    @classmethod
    def optional_model_strip(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    # OAuthトークン暗号化キー (AES-256用に32バイト推奨)
    token_encryption_key: str | None = Field(default=None)

    @field_validator("token_encryption_key", mode="before")
    @classmethod
    def validate_encryption_key_length(cls, v: object) -> str:
        if v is None or str(v).strip() == "":
            env = (
                os.getenv("ENVIRONMENT", os.getenv("NODE_ENV", "development"))
                .strip()
                .lower()
            )
            if env in ("production", "prod"):
                raise ValueError("本番環境では TOKEN_ENCRYPTION_KEY の設定が必須です！")
            logger.warning(
                "[Config] TOKEN_ENCRYPTION_KEY 未設定のため開発用ダミーキーを使用します。"
            )
            return "dev-dummy-encryption-key-32bytes!"

        v = str(v).strip()
        key_bytes = v.encode("utf-8")
        if len(key_bytes) < 32 and key_bytes.isascii():
            return v.ljust(32, "0")
        if len(key_bytes) == 32 and key_bytes.isascii():
            return v
        if key_bytes.isascii():
            return key_bytes[:32].decode("ascii")
        return hashlib.sha256(key_bytes).hexdigest()[:32]

    # 付箋ボード（02_1）のベースURL。タスクゴミ箱からは削除せず PATCH でグレー化する
    postit_board_url: str = "http://127.0.0.1:3000"
    # 付箋ボードのボードID（Board System でタスクになった付箋をここに反映する）
    postit_board_id: str = "wl"

    # Google カレンダー連携（OAuth 2.0）。未設定ならカレンダー連携は無効
    google_calendar_client_id: str | None = None
    google_calendar_client_secret: str | None = None
    google_calendar_redirect_uri: str | None = None
    calendar_timezone: str = "Asia/Tokyo"

    # OAuth 成功後のリダイレクト先のプレフィックス
    oauth_success_redirect_base: str = ""

    # 日次スケジュール
    scheduler_enabled: bool = True
    scheduler_news_interval_minutes: int = 0
    scheduler_calendar_interval_minutes: int = 30
    scheduler_base_url: str = "http://127.0.0.1:8000"
    reconciliation_dry_run: bool = True

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

    def resolve_ollama_for_target(
        self, target: int | None
    ) -> tuple[str | None, str | None]:
        if target is None:
            return self.ollama_url, self.ollama_model
        urls = {1: self.ollama_url_1, 2: self.ollama_url_2, 3: self.ollama_url_3}
        models = {
            1: self.ollama_model_1,
            2: self.ollama_model_2,
            3: self.ollama_model_3,
        }
        u = urls.get(target) or self.ollama_url
        m = models.get(target) or self.ollama_model
        return u, m

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        production_modes = {"production", "prod"}
        if (
            self.environment.strip().lower() in production_modes
            or os.getenv("NODE_ENV", "").strip().lower() in production_modes
        ):
            if self.admin_password == "admin123":
                raise ValueError(
                    "本番環境では ADMIN_PASSWORD を既定値から変更してください。"
                )
            if self.jwt_secret == "super-secret-key-change-in-production-12345":
                raise ValueError(
                    "本番環境では JWT_SECRET を安全な値に変更してください。"
                )
            if self.internal_api_secret == "wl-internal-secret-change-in-production":
                raise ValueError(
                    "本番環境では INTERNAL_API_SECRET を既定値から変更してください。"
                )
        t = self.llm_target
        if t is None:
            return self
        u, _ = self.resolve_ollama_for_target(t)
        if not u:
            raise ValueError(
                f"LLM_TARGET={t} のときは OLLAMA_URL_{t} か、フォールバック用の OLLAMA_URL を設定してください。"
            )
        return self

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

if settings.admin_password == "admin123":
    logger.warning(
        "WARNING: admin_password がデフォルト値 ('admin123') です。本番環境では .env で安全なパスワードに変更してください。"
    )
