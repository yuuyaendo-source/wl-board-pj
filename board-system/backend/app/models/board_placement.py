# -*- coding: utf-8 -*-
"""board_placements テーブル。付箋がどのボードのどこにあるかを管理。"""
from app.core.time_utils import utc_now_naive

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BoardType(str, enum.Enum):
    """ボード種別。"""

    TASK = "TASK"
    PERSONAL = "PERSONAL"
    MORNING = "MORNING"


class Lane(str, enum.Enum):
    """Personal Board のレーン。"""

    INBOX = "INBOX"
    TODAY = "TODAY"
    DONE = "DONE"
    HELP_REQUEST = "HELP_REQUEST"  # 応援要請（付箋を赤表示）


def _enum_values(e):
    return [x.value for x in e]


class BoardPlacement(Base):
    """付箋のボード配置。同一付箋が複数ボードにある場合は複数行。

    TASK 配置の position_x / position_y は画面描画座標ではなく、AI 自動仕分けで
    算出された緊急度 / 重要度（各 0〜100）の内部スコアを保持する。
    """

    __tablename__ = "board_placements"
    __table_args__ = (
        UniqueConstraint(
            "note_id", "board_type", "owner_id", name="uq_note_board_owner"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        ForeignKey("sticky_notes.id", ondelete="CASCADE"), nullable=False
    )
    board_type: Mapped[BoardType] = mapped_column(
        Enum(BoardType, values_callable=_enum_values, native_enum=False),
        nullable=False,
    )
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    lane: Mapped[Lane | None] = mapped_column(
        Enum(Lane, values_callable=_enum_values, native_enum=False),
        nullable=True,
    )
    # 画面描画座標ではなく、AI自動仕分けによる緊急度 (0-100) / 重要度 (0-100) の内部スコアを保持
    position_x: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="AIスコア: 緊急度(0-100)"
    )
    position_y: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="AIスコア: 重要度(0-100)"
    )
    matrix_quadrant: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now_naive)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now_naive, onupdate=utc_now_naive
    )
    # カレンダー更新で作成した Today 付箋（'calendar' 終日 | 'calendar_timed' 時刻付き | NULL）
    placement_source: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # 手動で Today に移動された場合 True。期限による自動移動をスキップするフラグ。
    is_manually_moved_to_today: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    note = relationship("StickyNote", back_populates="board_placements")
    owner = relationship("User", back_populates="board_placements_owned")
