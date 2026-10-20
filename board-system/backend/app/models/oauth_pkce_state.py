# -*- coding: utf-8 -*-
"""oauth_pkce_state: Google OAuth PKCE の code_verifier を一時保存（コールバック用）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OAuthPkceState(Base):
    """PKCE の state、ユーザー、code_verifier を一時保存する。"""

    __tablename__ = "oauth_pkce_state"

    state: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
