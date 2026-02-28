# -*- coding: utf-8 -*-
"""personal_summary_cache テーブル。linko-system の person_id 単位で summary/today を保持。"""
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PersonalSummaryCache(Base):
    """
    person_id（linko-system の UUID）をキーに、その日の events と today を保持。
    GET /api/personal/{person_id}/summary で返し、POST /api/personal/{person_id}/today で today を更新。
    """

    __tablename__ = "personal_summary_cache"

    person_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    events: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array
    today: Mapped[str] = mapped_column(Text, nullable=False, default="[]")   # JSON array
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
