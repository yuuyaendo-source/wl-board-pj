# -*- coding: utf-8 -*-
"""board_placements テーブル。付箋がどのボードのどこにあるかを管理。"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BoardType(str, enum.Enum):
    """ボード種別。"""
    MAIN = "MAIN"
    TASK = "TASK"
    PERSONAL = "PERSONAL"
    MORNING = "MORNING"


class Lane(str, enum.Enum):
    """Personal Board のレーン。"""
    INBOX = "INBOX"
    TODAY = "TODAY"
    DONE = "DONE"


def _enum_values(e):
    return [x.value for x in e]


class BoardPlacement(Base):
    """1付箋が1ボード上でどこに置かれているか。同一付箋が複数ボードにある場合は複数行。"""

    __tablename__ = "board_placements"
    __table_args__ = (
        UniqueConstraint("note_id", "board_type", "owner_id", name="uq_note_board_owner"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(ForeignKey("sticky_notes.id", ondelete="CASCADE"), nullable=False)
    board_type: Mapped[BoardType] = mapped_column(
        Enum(BoardType, values_callable=_enum_values, native_enum=False),
        nullable=False,
    )
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    lane: Mapped[Lane | None] = mapped_column(
        Enum(Lane, values_callable=_enum_values, native_enum=False),
        nullable=True,
    )
    position_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    position_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    matrix_quadrant: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    note = relationship("StickyNote", back_populates="board_placements")
    owner = relationship("User", back_populates="board_placements_owned")
