# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import BaseModel

from app.models.board_placement import BoardType, Lane


class BoardPlacementCreate(BaseModel):
    note_id: int
    board_type: BoardType
    owner_id: int | None = None
    lane: Lane | None = None
    position_x: float | None = None
    position_y: float | None = None
    sort_order: int = 0


class BoardPlacementUpdate(BaseModel):
    lane: Lane | None = None
    position_x: float | None = None
    position_y: float | None = None
    matrix_quadrant: int | None = None
    sort_order: int | None = None


class BoardPlacementResponse(BaseModel):
    id: int
    note_id: int
    board_type: BoardType
    owner_id: int | None
    lane: Lane | None
    position_x: float | None
    position_y: float | None
    matrix_quadrant: int | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MoveToPersonalBody(BaseModel):
    owner_id: int
    lane: Lane = Lane.INBOX


class BoardPlacementWithNoteResponse(BaseModel):
    """配置 + 付箋本文（ボード View 用）。Personal 用に is_from_task を付与。"""
    id: int
    note_id: int
    board_type: BoardType
    owner_id: int | None
    lane: Lane | None
    position_x: float | None
    position_y: float | None
    matrix_quadrant: int | None
    sort_order: int
    note_content: str
    note_status: str
    is_from_task: bool = False
