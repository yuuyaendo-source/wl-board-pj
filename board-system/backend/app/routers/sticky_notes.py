# -*- coding: utf-8 -*-
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import settings
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.schemas.board_placement import BoardPlacementResponse, MoveToPersonalBody
from app.schemas.sticky_note import (
    ImportFromPostitBody,
    ImportFromPostitResponse,
    StickyNoteCreate,
    StickyNoteResponse,
    StickyNoteUpdate,
)

router = APIRouter(prefix="/sticky_notes", tags=["sticky_notes"])


def _note_response(note: StickyNote) -> StickyNoteResponse:
    return StickyNoteResponse(
        id=note.id,
        content=note.content,
        author_id=note.author_id,
        status=note.status,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.get("", response_model=list[StickyNoteResponse])
async def list_sticky_notes(db: AsyncSession = Depends(get_db)):
    """付箋一覧。"""
    result = await db.execute(select(StickyNote).order_by(StickyNote.id.desc()))
    return [_note_response(n) for n in result.scalars().all()]


@router.post("/import_from_postit", response_model=ImportFromPostitResponse)
async def import_from_postit(body: ImportFromPostitBody, db: AsyncSession = Depends(get_db)):
    """付箋ボードから一括取り込み。重複はスキップ。取り込んだ各付箋は AI で自動振り分け（Task 列・担当者→Personal）。"""
    from app.models.sticky_note import NoteStatus
    from app.services.orchestrator import process_new_note_ai

    created = 0
    skipped = 0
    for item in body.notes:
        content = (item.text or "").strip()
        if not content:
            continue
        r = await db.execute(
            select(StickyNote).where(
                StickyNote.postit_board_id == body.board_id,
                StickyNote.postit_note_id == str(item.id),
            ).limit(1)
        )
        if r.scalar_one_or_none() is not None:
            skipped += 1
            continue
        note = StickyNote(
            content=content,
            author_id=None,
            status=NoteStatus.ACTIVE,
            postit_board_id=body.board_id,
            postit_note_id=str(item.id),
        )
        db.add(note)
        await db.flush()
        placement_main = BoardPlacement(
            note_id=note.id,
            board_type=BoardType.MAIN,
            owner_id=None,
            sort_order=0,
        )
        db.add(placement_main)
        await db.flush()
        created += 1
        # 取り込んだ付箋を AI で自動振り分け（Task の列・担当者→Personal）
        try:
            await process_new_note_ai(note.id, db)
        except Exception:
            pass  # 1件失敗しても他は続行
    return ImportFromPostitResponse(created=created, skipped=skipped)


@router.post("", response_model=StickyNoteResponse)
async def create_sticky_note(body: StickyNoteCreate, db: AsyncSession = Depends(get_db)):
    """付箋作成。Main Board に1件配置。postit_* あり時は付箋ボード連携用。"""
    from app.models.sticky_note import NoteStatus
    status = body.status if body.status is not None else NoteStatus.ACTIVE
    note = StickyNote(
        content=body.content,
        author_id=body.author_id,
        status=status,
        postit_board_id=body.postit_board_id,
        postit_note_id=body.postit_note_id,
    )
    db.add(note)
    await db.flush()
    placement = BoardPlacement(
        note_id=note.id,
        board_type=BoardType.MAIN,
        owner_id=None,
        sort_order=0,
    )
    db.add(placement)
    await db.flush()

    # personal_only でないときのみ AI 自動振り分け（Triage → Task 配置・Personal 配布）
    if not getattr(body, "personal_only", False):
        try:
            from app.services.orchestrator import process_new_note_ai

            await process_new_note_ai(note.id, db)
        except Exception:
            pass  # 付箋と Main 配置は作成済み。AI 失敗時は Task/Personal 配置をスキップ

    await db.commit()
    await db.refresh(note)
    return _note_response(note)


class CreatePersonalNoteBody(BaseModel):
    """パーソナルボードに直接投稿する際のリクエスト。create + move_to_personal を1トランザクションで行う。"""
    content: str
    owner_id: int
    lane: Lane = Lane.INBOX


@router.post("/create_personal", response_model=BoardPlacementResponse)
async def create_personal_note(
    body: CreatePersonalNoteBody,
    db: AsyncSession = Depends(get_db),
):
    """パーソナルボードに付箋を1件作成し、指定 owner の Personal に配置する。1リクエストで完結するため、複数インスタンスやコミットタイミングの影響を受けない。"""
    from app.models.sticky_note import NoteStatus

    user_result = await db.execute(select(User).where(User.id == body.owner_id))
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=400,
            detail=f"owner_id={body.owner_id} のユーザーが存在しません。",
        )
    note = StickyNote(
        content=body.content,
        author_id=None,
        status=NoteStatus.ACTIVE,
        postit_board_id=None,
        postit_note_id=None,
    )
    db.add(note)
    await db.flush()
    placement_main = BoardPlacement(
        note_id=note.id,
        board_type=BoardType.MAIN,
        owner_id=None,
        sort_order=0,
    )
    db.add(placement_main)
    await db.flush()
    placement_personal = BoardPlacement(
        note_id=note.id,
        board_type=BoardType.PERSONAL,
        owner_id=body.owner_id,
        lane=body.lane,
        sort_order=0,
    )
    db.add(placement_personal)
    await db.flush()
    await db.refresh(placement_personal)
    return BoardPlacementResponse(
        id=placement_personal.id,
        note_id=placement_personal.note_id,
        board_type=placement_personal.board_type,
        owner_id=placement_personal.owner_id,
        lane=placement_personal.lane,
        position_x=placement_personal.position_x,
        position_y=placement_personal.position_y,
        matrix_quadrant=placement_personal.matrix_quadrant,
        sort_order=placement_personal.sort_order,
        created_at=placement_personal.created_at,
        updated_at=placement_personal.updated_at,
    )


class SyncFromPostitBody(BaseModel):
    """付箋ボードの付箋テキストを Board System の該当付箋に反映する。"""
    board_id: str
    note_id: str
    content: str


@router.patch("/sync_from_postit", response_model=StickyNoteResponse)
async def sync_from_postit(body: SyncFromPostitBody, db: AsyncSession = Depends(get_db)):
    """付箋ボードで追記された内容を、Board System の該当付箋（postit_board_id + postit_note_id）に反映する。"""
    result = await db.execute(
        select(StickyNote).where(
            StickyNote.postit_board_id == body.board_id,
            StickyNote.postit_note_id == body.note_id,
        ).limit(1)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="No sticky note linked to this postit note")
    note.content = body.content
    await db.flush()
    await db.refresh(note)
    return _note_response(note)


@router.get("/{note_id}", response_model=StickyNoteResponse)
async def get_sticky_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """付箋1件取得。"""
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")
    return _note_response(note)


def _notify_postit_text(board_id: str, note_id: str, text: str) -> None:
    """付箋ボードの付箋テキストを更新（Board System で追記した内容を反映）。"""
    import json
    import urllib.request
    from app.config import settings
    url = f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception:
        pass


@router.patch("/{note_id}", response_model=StickyNoteResponse)
async def update_sticky_note(note_id: int, body: StickyNoteUpdate, db: AsyncSession = Depends(get_db)):
    """付箋の content / status を更新。付箋ボード連携付箋の場合は追記内容を付箋ボード側にも反映する。"""
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")
    if body.content is not None:
        note.content = body.content
    if body.status is not None:
        note.status = body.status
    await db.flush()
    await db.refresh(note)
    # 付箋ボード連携付箋の場合、追記内容を付箋ボード側に反映
    if body.content is not None and note.postit_board_id and note.postit_note_id:
        await asyncio.to_thread(_notify_postit_text, note.postit_board_id, note.postit_note_id, note.content)
    return _note_response(note)


def _notify_postit_archive(board_id: str, note_id: str) -> None:
    """付箋ボード（02_1）の付箋を削除せずグレー化。同期で呼ぶ。"""
    import json
    import urllib.request
    from app.config import settings
    url = f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    body = json.dumps({"gray": True}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception:
        pass


@router.delete("/by_postit", status_code=204)
async def delete_sticky_notes_by_postit(
    board_id: str = Query(..., description="付箋ボードの board_id (例: wl)"),
    note_id: str = Query(..., description="付箋ボード上の note id"),
    db: AsyncSession = Depends(get_db),
):
    """付箋ボードで付箋が削除されたときに呼ぶ。該当する Board System の付箋を削除。"""
    result = await db.execute(
        select(StickyNote).where(
            StickyNote.postit_board_id == board_id,
            StickyNote.postit_note_id == note_id,
        )
    )
    notes = list(result.scalars().all())
    for note in notes:
        await db.delete(note)
    await db.flush()
    return None


@router.delete("/{note_id}", status_code=204)
async def delete_sticky_note(note_id: int, db: AsyncSession = Depends(get_db)):
    """付箋削除。複数人が持っている場合は全員がDoneにするまで削除不可。付箋ボード連携時は 02_1 では削除せずグレー化（PATCH）。
    パスは sticky_note.id を想定。誤って board_placement.id が渡された場合も PERSONAL 配置から note_id を解決して削除する。"""
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        # フロントが placement.id を渡した場合のフォールバック: PERSONAL 配置から note_id を解決
        placement_result = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.id == note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
            ).limit(1)
        )
        placement = placement_result.scalar_one_or_none()
        if placement:
            note_id = placement.note_id
            result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
            note = result.scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=404, detail="Sticky note not found")

    # 複数人が持っている付箋は全員がDoneにするまで削除できない
    r = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    personal_placements = list(r.scalars().all())
    if len(personal_placements) >= 2:
        not_done = [p for p in personal_placements if p.lane != Lane.DONE]
        if not_done:
            raise HTTPException(
                status_code=409,
                detail="この付箋は複数人が持っています。全員がDoneにするまで削除できません。",
            )

    postit_board_id = note.postit_board_id
    postit_note_id = note.postit_note_id
    await db.delete(note)
    await db.flush()
    if postit_board_id and postit_note_id:
        await asyncio.to_thread(_notify_postit_archive, postit_board_id, postit_note_id)
    return None


@router.post("/{note_id}/move_to_personal", response_model=BoardPlacementResponse)
async def move_to_personal(
    note_id: int,
    body: MoveToPersonalBody,
    db: AsyncSession = Depends(get_db),
):
    """付箋を Personal Board に配置する。既に同じ (note_id, PERSONAL, owner_id) があれば lane を更新。"""
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")
    # owner_id は users.id の外部キー。ユーザーが存在しないと DB エラーになるため事前チェック
    user_result = await db.execute(select(User).where(User.id == body.owner_id))
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=400,
            detail=f"owner_id={body.owner_id} のユーザーが存在しません。パーソナルボードを使うには users テーブルに該当 ID のユーザーが必要です。",
        )
    r = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == body.owner_id,
        )
    )
    placement = r.scalar_one_or_none()
    if placement:
        placement.lane = body.lane
        await db.flush()
        await db.refresh(placement)
    else:
        placement = BoardPlacement(
            note_id=note_id,
            board_type=BoardType.PERSONAL,
            owner_id=body.owner_id,
            lane=body.lane,
            sort_order=0,
        )
        db.add(placement)
        await db.flush()
        await db.refresh(placement)
    return BoardPlacementResponse(
        id=placement.id,
        note_id=placement.note_id,
        board_type=placement.board_type,
        owner_id=placement.owner_id,
        lane=placement.lane,
        position_x=placement.position_x,
        position_y=placement.position_y,
        matrix_quadrant=placement.matrix_quadrant,
        sort_order=placement.sort_order,
        created_at=placement.created_at,
        updated_at=placement.updated_at,
    )


@router.post("/{note_id}/release_to_task_board", response_model=BoardPlacementResponse)
async def release_to_task_board(note_id: int, db: AsyncSession = Depends(get_db)):
    """付箋を Task Board に配置する。既に TASK 配置があればそのまま返す。
    パーソナル投稿をリリースした場合は当該付箋の Personal 配置を削除し、タスクボードでは黄色（未引き取り）で表示する。"""
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")
    r = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.TASK,
            BoardPlacement.owner_id.is_(None),
        )
    )
    placement = r.scalar_one_or_none()
    if placement:
        await db.refresh(placement)
    else:
        placement = BoardPlacement(
            note_id=note_id,
            board_type=BoardType.TASK,
            owner_id=None,
            sort_order=0,
        )
        db.add(placement)
        await db.flush()
        await db.refresh(placement)
    # パーソナル投稿をリリースした場合：Personal 配置を削除し、タスクボードで黄色（誰でも引き継げる状態）にする
    await db.execute(
        delete(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    await db.flush()

    # 付箋ボード連携なしの付箋がタスクになったら付箋ボードに反映
    if not note.postit_note_id:
        from app.services.orchestrator import _sync_note_to_postit_sync
        ok = await asyncio.to_thread(
            _sync_note_to_postit_sync,
            note.id,
            note.content or "",
            settings.postit_board_id,
            settings.postit_board_url,
        )
        if ok:
            note.postit_board_id = settings.postit_board_id
            note.postit_note_id = f"bs-{note.id}"
            await db.flush()

    return BoardPlacementResponse(
        id=placement.id,
        note_id=placement.note_id,
        board_type=placement.board_type,
        owner_id=placement.owner_id,
        lane=placement.lane,
        position_x=placement.position_x,
        position_y=placement.position_y,
        matrix_quadrant=placement.matrix_quadrant,
        sort_order=placement.sort_order,
        created_at=placement.created_at,
        updated_at=placement.updated_at,
    )
