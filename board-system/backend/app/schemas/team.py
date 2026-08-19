# -*- coding: utf-8 -*-
"""チームスキーマ。"""
from datetime import datetime

from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str


class TeamUpdate(BaseModel):
    name: str | None = None


class TeamResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}
