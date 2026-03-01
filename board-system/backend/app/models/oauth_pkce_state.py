# -*- coding: utf-8 -*-
"""oauth_pkce_state: Google OAuth PKCE の code_verifier を一時保存（コールバック用）。"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class OAuthPkceState(Base):
    """PKCE の state -> code_verifier を保存。コールバックで使用後に削除。"""

    __tablename__ = "oauth_pkce_state"

    state: Mapped[str] = mapped_column(String(64), primary_key=True)
    code_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
