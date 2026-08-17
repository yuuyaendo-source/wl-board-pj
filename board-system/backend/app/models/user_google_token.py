# -*- coding: utf-8 -*-
"""user_google_tokens テーブル。ユーザーごとの Google カレンダー OAuth トークン。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from app.config import settings
from app.db import Base


class UserGoogleToken(Base):
    """ユーザーに紐づく Google OAuth トークン（カレンダー取得用・暗号化保存）。"""

    __tablename__ = "user_google_tokens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # データベース上は平文ではなくAES暗号化された文字列として保存されます
    access_token: Mapped[str] = mapped_column(
        StringEncryptedType(
            Text,
            lambda: settings.token_encryption_key,
            AesEngine,
            "pkcs5",
        ),
        nullable=False,
    )

    refresh_token: Mapped[str | None] = mapped_column(
        StringEncryptedType(
            Text,
            lambda: settings.token_encryption_key,
            AesEngine,
            "pkcs5",
        ),
        nullable=True,
    )

    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
