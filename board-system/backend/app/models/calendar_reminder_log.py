# -*- coding: utf-8 -*-
"""カレンダーリマインドの送信ログ（Google 予定・15分前など）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CalendarReminderLog(Base):
    """1ユーザー・1予定・1日・1リマインド種別につき1行。"""

    __tablename__ = "calendar_reminder_logs"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "event_id", "remind_date", "remind_kind",
            name="uq_cal_remind_user_event_date_kind",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    remind_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD (Asia/Tokyo)
    remind_kind: Mapped[str] = mapped_column(String(16), nullable=False, default="before_15")
    event_summary: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
