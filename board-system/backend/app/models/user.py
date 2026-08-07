# -*- coding: utf-8 -*-
"""users テーブル。共通ユーザー管理: 名前・Eメール・呼び名。顔画像は user_faces で複数枚保持。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    """ユーザー。表示名・Eメール・呼び名・役割。Linko と共通で管理。"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    call_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    interest_vector: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 所属チーム（NULL = チーム未所属）
    team_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # リレーション
    sticky_notes = relationship("StickyNote", back_populates="author", foreign_keys="StickyNote.author_id")
    board_placements_owned = relationship("BoardPlacement", back_populates="owner", foreign_keys="BoardPlacement.owner_id")
    faces = relationship("UserFace", back_populates="user", cascade="all, delete-orphan")
    team = relationship("Team", back_populates="users", foreign_keys=[team_id])
