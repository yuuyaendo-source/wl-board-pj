# -*- coding: utf-8 -*-
"""user_faces テーブル。1ユーザーあたり複数枚の顔画像（カメラ・アップロード両対応）。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class UserFace(Base):
    """ユーザーに紐づく顔画像1枚。複数枚登録可。"""

    __tablename__ = "user_faces"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    image_data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    source: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "camera" | "upload" 等
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="faces")
