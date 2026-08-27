# -*- coding: utf-8 -*-
"""teams テーブル。メンバーをグループ化するチーム概念。"""
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Team(Base):
    """チーム。複数のユーザーをグループ化する。"""

    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # リレーション: チームに所属するユーザー（多対多）
    users = relationship(
        "User", secondary="user_teams", back_populates="teams", lazy="selectin"
    )
