# -*- coding: utf-8 -*-
"""user_google_tokens テーブル。ユーザーごとの Google カレンダー OAuth トークン。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UserGoogleToken(Base):
    """ユーザーに紐づく Google OAuth トークン（カレンダー取得用）。"""

    __tablename__ = "user_google_tokens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーションは User 側に backref を足すか、ここでは省略可
