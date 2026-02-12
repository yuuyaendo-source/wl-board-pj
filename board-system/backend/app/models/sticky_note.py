# -*- coding: utf-8 -*-
"""sticky_notes テーブル。付箋本文・投稿者・ステータス。"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text  # String for postit_*
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class NoteStatus(str, enum.Enum):
    """付箋のライフサイクル状態。"""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class StickyNote(Base):
    """付箋。1つの本文とステータス。複数ボードへの配置は board_placements で管理。"""

    __tablename__ = "sticky_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # 付箋ボード（02_1）取り込み元。削除連携用
    postit_board_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    postit_note_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[NoteStatus] = mapped_column(
        Enum(NoteStatus, values_callable=lambda x: [e.value for e in x], native_enum=False),
        nullable=False,
        default=NoteStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="sticky_notes")
    board_placements = relationship("BoardPlacement", back_populates="note", cascade="all, delete-orphan")
