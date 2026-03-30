# -*- coding: utf-8 -*-
"""システム全体の設定（1行）。LLM 切替など。id は常に 1。"""
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    # NULL = DB では上書きしない（環境変数 LLM_TARGET を使用）
    llm_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
