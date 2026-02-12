# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import BaseModel

from app.models.sticky_note import NoteStatus


class StickyNoteCreate(BaseModel):
    content: str
    author_id: int | None = None
    status: NoteStatus | None = None
    postit_board_id: str | None = None
    postit_note_id: str | None = None


class StickyNoteUpdate(BaseModel):
    content: str | None = None
    status: NoteStatus | None = None


class StickyNoteResponse(BaseModel):
    id: int
    content: str
    author_id: int | None
    status: NoteStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StickyNoteWithPlacementsResponse(StickyNoteResponse):
    """付箋 + 配置一覧（ボード View 用）。"""
    pass  # 同じ形。配置は別リストで返すか、ネストするかは API 次第


class ImportFromPostitItem(BaseModel):
    """付箋ボードの付箋1件。"""
    id: str
    text: str


class ImportFromPostitBody(BaseModel):
    """付箋ボードから一括取り込み。"""
    board_id: str
    notes: list[ImportFromPostitItem]


class ImportFromPostitResponse(BaseModel):
    """取り込み結果。重複はスキップ。"""
    created: int
    skipped: int
