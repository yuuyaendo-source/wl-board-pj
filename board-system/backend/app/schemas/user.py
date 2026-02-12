# -*- coding: utf-8 -*-
from pydantic import BaseModel


class UserCreate(BaseModel):
    name: str
    role: str | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    role: str | None

    model_config = {"from_attributes": True}
