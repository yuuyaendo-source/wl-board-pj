# -*- coding: utf-8 -*-
"""users テーブル。"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    """ユーザー。表示名・役割・将来のレコメンド用ベクトル。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    interest_vector: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON or 埋め込み文字列（将来用）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション（逆参照用）
    sticky_notes = relationship("StickyNote", back_populates="author", foreign_keys="StickyNote.author_id")
    board_placements_owned = relationship("BoardPlacement", back_populates="owner", foreign_keys="BoardPlacement.owner_id")
