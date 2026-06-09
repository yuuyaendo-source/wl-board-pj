# -*- coding: utf-8 -*-
"""タスクリマインドの送信・応答ログ（Personal Today 用）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TaskReminderLog(Base):
    """1ユーザー・1付箋・1日・1スロットにつき1行。shown 後に continue/done で更新。"""

    __tablename__ = "task_reminder_logs"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "note_id", "remind_date", "slot",
            name="uq_task_remind_user_note_date_slot",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note_id: Mapped[int] = mapped_column(ForeignKey("sticky_notes.id", ondelete="CASCADE"), nullable=False)
    placement_id: Mapped[int] = mapped_column(ForeignKey("board_placements.id", ondelete="CASCADE"), nullable=False)
    remind_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD (Asia/Tokyo)
    slot: Mapped[str] = mapped_column(String(5), nullable=False)  # "13:00"
    action: Mapped[str | None] = mapped_column(String(16), nullable=True)  # continue | done | None=表示のみ
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    acked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
