# -*- coding: utf-8 -*-
from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    email: str | None = None
    call_name: str | None = None
    role: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    call_name: str | None = None
    role: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str | None
    call_name: str | None
    role: str | None
    face_count: int = 0

    model_config = {"from_attributes": True}
