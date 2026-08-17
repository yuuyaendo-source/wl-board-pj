# -*- coding: utf-8 -*-
import asyncio
from datetime import date as DateType, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from app.config import settings
from pydantic import BaseModel
from sqlalchemy import delete, select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.schemas.board_placement import BoardPlacementResponse, MoveToPersonalBody
from app.schemas.sticky_note import (
    CopyToTeamBody,
    CopyToTeamResponse,
    ImportFromPostitBody,
    ImportFromPostitResponse,
    StickyNoteCreate,
    StickyNoteResponse,
    StickyNoteUpdate,
)

router = APIRouter(prefix="/sticky_notes", tags=["sticky_notes"])


def _get_jst_today() -> DateType:
    """JST基準の現在日付を取得"""
    return datetime.now(ZoneInfo("Asia/Tokyo")).date()


async def apply_due_date_rules_for_note(note_id: int, db: AsyncSession) -> None:
    """改善計画6に基づく期限連動移動ロジック:
    - DONE レーンにある配置は絶対に対象外（何もしない）
    - is_manually_moved_to_today が True の配置は判定をスキップ
    - days <= 0 (期限切れ・今日): TODAY
    - 0 < days < 30 (短期): [1, 2, 3, 4, 5, 10, 20] 日前なら TODAY、それ以外は INBOX
    - days >= 30 (長期): days % 30 == 0 なら TODAY、それ以外は INBOX
    """
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        return

    placements_res = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    placements = list(placements_res.scalars().all())
    if not placements:
        return

    today = _get_jst_today()

    for p in placements:
        # DONE レーンにあるタスクは期限切れであっても移動しない
        if p.lane == Lane.DONE or p.lane == "DONE":
            continue
        # 手動移動済みフラグが ON の場合はスキップ
        if p.is_manually_moved_to_today:
            continue

        if not note.due_date:
            # 期限がクリアされた場合、TODAY にあれば INBOX に戻す
            if p.lane == Lane.TODAY:
                p.lane = Lane.INBOX
            continue

        days = (note.due_date - today).days

        should_be_today = False
        if days <= 0:
            should_be_today = True
        elif days < 30:
            if days in [1, 2, 3, 4, 5, 10, 20]:
                should_be_today = True
        else:
            if days % 30 == 0:
                should_be_today = True

        new_lane = Lane.TODAY if should_be_today else Lane.INBOX
        if p.lane != new_lane:
            p.lane = new_lane

    await db.flush()


def _note_response(note: StickyNote) -> StickyNoteResponse:
    due_date_str = (
        note.due_date.isoformat() if getattr(note, "due_date", None) else None
    )
    return StickyNoteResponse(
        id=note.id,
        content=note.content,
        author_id=note.author_id,
        status=note.status,
        due_date=due_date_str,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


@router.get("", response_model=list[StickyNoteResponse])
async def list_sticky_notes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StickyNote).order_by(StickyNote.id.desc()))
    return [_note_response(n) for n in result.scalars().all()]


@router.post("/import_from_postit", response_model=ImportFromPostitResponse)
async def import_from_postit(
    body: ImportFromPostitBody, db: AsyncSession = Depends(get_db)
):
    from app.models.sticky_note import NoteStatus
    from app.services.orchestrator import process_new_note_ai

    created = 0
    skipped = 0
    for item in body.notes:
        content = (item.text or "").strip()
        if not content:
            continue
        r = await db.execute(
            select(StickyNote)
            .where(
                StickyNote.postit_board_id == body.board_id,
                StickyNote.postit_note_id == str(item.id),
            )
            .limit(1)
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
        try:
            await process_new_note_ai(note.id, db)
        except Exception:
            pass
    return ImportFromPostitResponse(created=created, skipped=skipped)


@router.post("", response_model=StickyNoteResponse)
async def create_sticky_note(
    body: StickyNoteCreate, db: AsyncSession = Depends(get_db)
):
    from app.models.sticky_note import NoteStatus

    status = body.status if body.status is not None else NoteStatus.ACTIVE

    parsed_due_date = None
    if body.due_date:
        try:
            parsed_due_date = DateType.fromisoformat(body.due_date)
        except ValueError:
            pass

    note = StickyNote(
        content=body.content,
        author_id=body.author_id,
        status=status,
        postit_board_id=body.postit_board_id,
        postit_note_id=body.postit_note_id,
        due_date=parsed_due_date,
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

    if not getattr(body, "personal_only", False):
        try:
            from app.services.orchestrator import process_new_note_ai

            await process_new_note_ai(note.id, db)
        except Exception:
            pass

    # AI等で割り当てられたパーソナル配置に期限ルールを自動適用
    await apply_due_date_rules_for_note(note.id, db)

    await db.commit()
    await db.refresh(note)
    return _note_response(note)


class CreatePersonalNoteBody(BaseModel):
    content: str
    owner_id: int
    lane: Lane = Lane.INBOX
    due_date: str | None = None


@router.post("/create_personal", response_model=BoardPlacementResponse)
async def create_personal_note(
    body: CreatePersonalNoteBody,
    db: AsyncSession = Depends(get_db),
):
    from app.models.sticky_note import NoteStatus

    user_result = await db.execute(select(User).where(User.id == body.owner_id))
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=400,
            detail=f"owner_id={body.owner_id} のユーザーが存在しません。",
        )

    parsed_due_date = None
    if body.due_date:
        try:
            parsed_due_date = DateType.fromisoformat(body.due_date)
        except ValueError:
            pass

    note = StickyNote(
        content=body.content,
        author_id=None,
        status=NoteStatus.ACTIVE,
        postit_board_id=None,
        postit_note_id=None,
        due_date=parsed_due_date,
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

    # 期限ルール適用（今日・期限切れ等なら TODAY に変更）
    await apply_due_date_rules_for_note(note.id, db)

    await db.commit()
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
    board_id: str
    note_id: str
    content: str


@router.patch("/sync_from_postit", response_model=StickyNoteResponse)
async def sync_from_postit(
    body: SyncFromPostitBody, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StickyNote)
        .where(
            StickyNote.postit_board_id == body.board_id,
            StickyNote.postit_note_id == body.note_id,
        )
        .limit(1)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=404, detail="No sticky note linked to this postit note"
        )
    note.content = body.content
    await db.flush()
    await db.refresh(note)
    return _note_response(note)


@router.get("/{note_id}", response_model=StickyNoteResponse)
async def get_sticky_note(note_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")
    return _note_response(note)


def _notify_postit_text(board_id: str, note_id: str, text: str) -> None:
    import json
    import urllib.request
    from app.config import settings

    url = (
        f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    )
    body = json.dumps({"text": text}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="PATCH")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception:
        pass


@router.patch("/{note_id}", response_model=StickyNoteResponse)
async def update_sticky_note(
    note_id: int, body: StickyNoteUpdate, db: AsyncSession = Depends(get_db)
):
    """付箋の content / status / due_date を更新。
    - due_date 変更時、is_manually_moved_to_today フラグを False に一括リセット
    - 改善計画6のルールに従い、パーソナル配置のレーンを自動判定して移動
    """
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    if body.content is not None:
        note.content = body.content
    if body.status is not None:
        note.status = body.status

    due_date_changed = False
    if body.due_date is not None:
        if body.due_date == "":
            if note.due_date is not None:
                note.due_date = None
                due_date_changed = True
        else:
            try:
                parsed_date = DateType.fromisoformat(body.due_date)
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="due_date は YYYY-MM-DD 形式で指定してください",
                )
            if note.due_date != parsed_date:
                note.due_date = parsed_date
                due_date_changed = True

    await db.flush()

    if due_date_changed:
        # 手動移動フラグの一括リセット（改善計画6）
        await db.execute(
            sa_update(BoardPlacement)
            .where(BoardPlacement.note_id == note_id)
            .values(is_manually_moved_to_today=False)
        )
        await db.flush()
        # 最新の due_date に基づきパーソナル配置のレーンルールを適用
        await apply_due_date_rules_for_note(note_id, db)

    await db.commit()
    await db.refresh(note)

    if body.content is not None and note.postit_board_id and note.postit_note_id:
        await asyncio.to_thread(
            _notify_postit_text, note.postit_board_id, note.postit_note_id, note.content
        )
    return _note_response(note)


def _notify_postit_archive(board_id: str, note_id: str) -> None:
    import json
    import urllib.request
    from app.config import settings

    url = (
        f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    )
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
    board_id: str = Query(..., description="付箋ボードの board_id"),
    note_id: str = Query(..., description="付箋ボード上の note id"),
    db: AsyncSession = Depends(get_db),
):
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
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        placement_result = await db.execute(
            select(BoardPlacement)
            .where(
                BoardPlacement.id == note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
            )
            .limit(1)
        )
        placement = placement_result.scalar_one_or_none()
        if placement:
            note_id = placement.note_id
            result = await db.execute(
                select(StickyNote).where(StickyNote.id == note_id)
            )
            note = result.scalar_one_or_none()
        if not note:
            raise HTTPException(status_code=404, detail="Sticky note not found")

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
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    user_result = await db.execute(select(User).where(User.id == body.owner_id))
    if user_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=400,
            detail=f"owner_id={body.owner_id} のユーザーが存在しません。",
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

    await db.execute(
        delete(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    await db.flush()

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


@router.post("/{note_id}/copy_to_team", response_model=CopyToTeamResponse)
async def copy_to_team(
    note_id: int,
    body: CopyToTeamBody,
    db: AsyncSession = Depends(get_db),
):
    from app.models.team import Team
    from app.models.board_placement import Lane as LaneEnum

    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    from sqlalchemy.orm import selectinload

    team_result = await db.execute(
        select(Team).options(selectinload(Team.users)).where(Team.id == body.team_id)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    members = team.users or []
    if not members:
        raise HTTPException(
            status_code=400, detail="チームに所属するメンバーがいません"
        )

    try:
        lane_value = LaneEnum(body.lane)
    except ValueError:
        lane_value = LaneEnum.INBOX

    created_user_ids: list[int] = []
    for member in members:
        owner_id = member.id
        r = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.owner_id == owner_id,
            )
        )
        placement = r.scalar_one_or_none()
        if placement:
            placement.lane = lane_value
        else:
            placement = BoardPlacement(
                note_id=note_id,
                board_type=BoardType.PERSONAL,
                owner_id=owner_id,
                lane=lane_value,
                sort_order=0,
            )
            db.add(placement)
            created_user_ids.append(owner_id)
        await db.flush()

    member_count = len(members)
    message = f"{team.name} チーム全員（{member_count}名）にコピーしました"
    return CopyToTeamResponse(
        created=len(created_user_ids),
        user_ids=[m.id for m in members],
        message=message,
    )
