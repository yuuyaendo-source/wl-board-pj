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
    """True のとき AI 振り分けをスキップ（パーソナル投稿のみで Task に載せない）。"""
    personal_only: bool | None = None
    due_date: str | None = None  # YYYY-MM-DD 形式


class StickyNoteUpdate(BaseModel):
    content: str | None = None
    status: NoteStatus | None = None
    due_date: str | None = (
        None  # YYYY-MM-DD 形式。空文字列「""」で送信すると期限をクリア。
    )


class StickyNoteResponse(BaseModel):
    id: int
    content: str
    author_id: int | None
    status: NoteStatus
    due_date: str | None = None  # YYYY-MM-DD 形式。
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StickyNoteWithPlacementsResponse(StickyNoteResponse):
    """付箋 + 配置一覧（ボード View 用）。"""

    pass


class ImportFromPostitItem(BaseModel):
    """付箋ボードの付箋1件。"""

    id: str
    text: str
    due_date: str | None = None  # YYYY-MM-DD 形式


class ImportFromPostitBody(BaseModel):
    """付箋ボードから一括取り込み。"""

    board_id: str
    notes: list[ImportFromPostitItem]


class ImportFromPostitResponse(BaseModel):
    """取り込み結果。重複はスキップ。"""

    created: int
    skipped: int


class CopyToTeamBody(BaseModel):
    """チーム全員にコピーするリクエスト。"""

    team_id: int
    lane: str = "INBOX"


class CopyToTeamResponse(BaseModel):
    """チームコピー結果。"""

    created: int
    user_ids: list[int]
    message: str
