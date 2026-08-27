# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import List, Optional


class UserCreate(BaseModel):
    name: str
    email: str | None = None
    call_name: str | None = None
    role: str | None = None
    team_ids: List[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    call_name: str | None = None
    role: str | None = None
    team_ids: Optional[List[int]] = None


class TeamSummary(BaseModel):
    id: int
    name: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str | None
    call_name: str | None
    role: str | None
    # 後方互換用: クライアントが単一 team_id に依存している場合に備え、最初のチームIDを返す
    team_id: int | None = None
    team_ids: List[int] = Field(default_factory=list)
    teams: List[TeamSummary] = Field(default_factory=list)
    face_count: int = 0

    model_config = {"from_attributes": True}
