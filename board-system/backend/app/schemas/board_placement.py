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
    placement_source: str | None = None
    is_manually_moved_to_today: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MoveToPersonalBody(BaseModel):
    owner_id: int
    lane: Lane = Lane.INBOX


class ReorderPersonalLaneBody(BaseModel):
    """同一レーン内の並び替え。placement_ids の順に sort_order を 0,1,2,... で設定する。"""
    owner_id: int
    lane: Lane
    placement_ids: list[int]


class TakenByUser(BaseModel):
    """Task 付箋をパーソナルに引き取ったユーザー（アイコン表示用）。"""
    id: int
    name: str
    name_short: str  # 例: 浅川久司 → 浅


class BoardPlacementWithNoteResponse(BaseModel):
    """配置 + 付箋本文（ボード View 用）。Personal 用 is_from_task、Task 用 taken_by / task_color。"""
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
    placement_source: str | None = None  # MORNING で 'news' のときニュース枠用
    is_from_task: bool = False
    # Task 用: 誰が引き取ったか・付箋の色（yellow=未引き取り, green=引き取り中, grey=Done, red=応援要請）
    taken_by: list[TakenByUser] = []
    task_color: str = "yellow"  # "yellow" | "green" | "grey" | "red"
    is_accepted_by_others: bool = False
    is_manually_moved_to_today: bool = False
    # 紐づく付箋の期限（YYYY-MM-DD 文字列）
    due_date: str | None = None
