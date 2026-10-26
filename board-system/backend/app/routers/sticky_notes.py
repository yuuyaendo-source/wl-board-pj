# -*- coding: utf-8 -*-
import logging
from datetime import date as DateType

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.core.time_utils import now_jst
from app.models import BoardPlacement, BoardType, StickyNote, Team, User
from app.models.board_placement import Lane
from app.models.sticky_note import NoteStatus
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
from app.services.due_date_rules import should_move_to_today
from app.services.orchestrator import ensure_postit_sync as _ensure_postit_sync

router = APIRouter(prefix="/sticky_notes", tags=["sticky_notes"])
logger = logging.getLogger(__name__)


def _get_jst_today() -> DateType:
    """JST基準の現在日付を取得"""
    return now_jst().date()


async def apply_due_date_rules_for_note(note_id: int, db: AsyncSession) -> None:
    """期限連動移動ロジック（完了・応援要請は除外）"""
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
        # DONE および HELP_REQUEST（応援要請）レーンにある配置は自動移動の対象外とする
        if p.lane in (Lane.DONE, Lane.HELP_REQUEST):
            continue
        if p.is_manually_moved_to_today:
            continue

        should_be_today = should_move_to_today(note.due_date, today)
        p.lane = Lane.TODAY if should_be_today else Lane.INBOX

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
        is_personal_only=getattr(note, "is_personal_only", False),
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


async def _notify_postit_note_async(
    request: Request,
    board_id: str,
    note_id: str,
    text: str | None = None,
    due_date: str | None = None,
) -> None:
    """request.app.state から共有クライアントを取得し非同期で付箋ボードへ通知。"""
    url = (
        f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    )
    payload = {}
    if text is not None:
        payload["text"] = text
    if due_date is not None:
        payload["due_date"] = due_date

    if not payload:
        return

    try:
        client = request.app.state.http_client
        await client.patch(url, json=payload, timeout=5.0)
    except Exception as e:
        logger.warning(f"付箋ボード更新通知失敗: {e}")


async def _notify_postit_gray_async(
    request: Request, board_id: str, note_id: str, gray: bool = True
) -> bool:
    """request.app.state から共有クライアントを取得し非同期でグレー化/解除通知を送信。"""
    url = (
        f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    )
    try:
        client = request.app.state.http_client
        resp = await client.patch(url, json={"gray": gray}, timeout=5.0)
        return 200 <= resp.status_code < 300
    except Exception as e:
        logger.warning(f"グレー状態({gray})通知送信失敗: {e}")
        return False


async def _notify_postit_archive_async(
    request: Request, board_id: str, note_id: str
) -> bool:
    """request.app.state から共有クライアントを取得し非同期でグレー化通知を送信。"""
    return await _notify_postit_gray_async(request, board_id, note_id, gray=True)


@router.get("", response_model=list[StickyNoteResponse])
async def get_sticky_notes(
    board_type: BoardType | None = Query(None),
    owner_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(StickyNote)
    if board_type or owner_id is not None:
        stmt = stmt.join(BoardPlacement, StickyNote.id == BoardPlacement.note_id)
        if board_type:
            stmt = stmt.where(BoardPlacement.board_type == board_type)
        if owner_id is not None:
            stmt = stmt.where(BoardPlacement.owner_id == owner_id)
    result = await db.execute(stmt)
    notes = result.scalars().all()
    return [_note_response(n) for n in notes]


@router.post("/import_from_postit", response_model=ImportFromPostitResponse)
async def import_from_postit(
    body: ImportFromPostitBody, db: AsyncSession = Depends(get_db)
):
    import_count = 0
    skip_count = 0

    for item in body.notes:
        parsed_due_date = None
        if item.due_date:
            try:
                parsed_due_date = DateType.fromisoformat(item.due_date)
            except ValueError:
                pass

        result = await db.execute(
            select(StickyNote).where(
                StickyNote.postit_board_id == body.board_id,
                StickyNote.postit_note_id == str(item.id),
            )
        )
        existing_note = result.scalar_one_or_none()

        if existing_note:
            if item.due_date is not None and existing_note.due_date != parsed_due_date:
                existing_note.due_date = parsed_due_date
                await db.flush()
                await apply_due_date_rules_for_note(existing_note.id, db)
            skip_count += 1
            continue

        note = StickyNote(
            content=item.text or "（テキストなし）",
            postit_board_id=body.board_id,
            postit_note_id=str(item.id),
            due_date=parsed_due_date,
            is_personal_only=False,
        )
        db.add(note)
        await db.flush()

        placement = BoardPlacement(
            note_id=note.id,
            board_type=BoardType.TASK,
            matrix_quadrant=1,
            sort_order=0,
            placement_source="postit",
        )
        db.add(placement)
        import_count += 1
    return ImportFromPostitResponse(created=import_count, skipped=skip_count)


@router.post("", response_model=StickyNoteResponse, status_code=201)
async def create_sticky_note(
    request: Request,
    body: StickyNoteCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    parsed_due_date = None
    if body.due_date:
        try:
            parsed_due_date = DateType.fromisoformat(body.due_date)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="due_date は YYYY-MM-DD 形式で指定してください",
            )

    note = StickyNote(
        content=body.content,
        author_id=body.author_id,
        postit_board_id=body.postit_board_id,
        postit_note_id=body.postit_note_id,
        status=body.status or NoteStatus.ACTIVE,
        due_date=parsed_due_date,
        is_personal_only=(
            body.personal_only if body.personal_only is not None else False
        ),
    )
    db.add(note)
    await db.flush()

    if not note.is_personal_only:
        from app.services.orchestrator import process_new_note_ai_background

        background_tasks.add_task(process_new_note_ai_background, request.app, note.id)
    elif note.author_id:
        placement = BoardPlacement(
            note_id=note.id,
            board_type=BoardType.PERSONAL,
            owner_id=note.author_id,
            lane=Lane.INBOX,
            sort_order=0,
        )
        db.add(placement)
        await db.flush()
        await apply_due_date_rules_for_note(note.id, db)
        await db.refresh(note)

    return _note_response(note)


class CreatePersonalNoteBody(BaseModel):
    owner_id: int
    content: str
    due_date: str | None = None
    lane: Lane | None = None


@router.post("/create_personal", response_model=StickyNoteResponse, status_code=201)
async def create_personal_note(
    body: CreatePersonalNoteBody, db: AsyncSession = Depends(get_db)
):
    """パーソナルボードから直接付箋を作成する。"""
    result = await db.execute(select(User).where(User.id == body.owner_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    parsed_due_date = None
    if body.due_date:
        try:
            parsed_due_date = DateType.fromisoformat(body.due_date)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="due_date は YYYY-MM-DD 形式で指定してください",
            )

    note = StickyNote(
        content=body.content,
        author_id=body.owner_id,
        postit_board_id=None,
        postit_note_id=None,
        due_date=parsed_due_date,
        is_personal_only=True,
    )
    db.add(note)
    await db.flush()

    is_manual = body.lane == Lane.TODAY
    initial_lane = body.lane or Lane.INBOX

    placement = BoardPlacement(
        note_id=note.id,
        board_type=BoardType.PERSONAL,
        owner_id=body.owner_id,
        lane=initial_lane,
        sort_order=0,
        is_manually_moved_to_today=is_manual,
    )
    db.add(placement)
    await db.flush()

    await apply_due_date_rules_for_note(note.id, db)
    await db.refresh(note)
    return _note_response(note)


class SyncFromPostitBody(BaseModel):
    board_id: str
    note_id: str
    content: str | None = None
    due_date: str | None = None


@router.patch("/sync_from_postit", response_model=StickyNoteResponse)
async def sync_from_postit(
    body: SyncFromPostitBody, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(StickyNote).where(
            StickyNote.postit_board_id == body.board_id,
            StickyNote.postit_note_id == body.note_id,
        )
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(
            status_code=404, detail="No sticky note linked to this postit note"
        )

    if body.content is not None:
        note.content = body.content

    if "due_date" in body.model_fields_set:
        parsed_due_date = None
        if body.due_date is not None and body.due_date != "":
            try:
                parsed_due_date = DateType.fromisoformat(body.due_date)
            except ValueError:
                pass
        if note.due_date != parsed_due_date:
            note.due_date = parsed_due_date
            await db.execute(
                sa_update(BoardPlacement)
                .where(BoardPlacement.note_id == note.id)
                .values(is_manually_moved_to_today=False)
            )
            await db.flush()
            await apply_due_date_rules_for_note(note.id, db)

    await db.refresh(note)
    return _note_response(note)


@router.get("/{note_id}", response_model=StickyNoteResponse)
async def get_sticky_note(note_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")
    return _note_response(note)


@router.patch("/{note_id}", response_model=StickyNoteResponse)
async def update_sticky_note(
    request: Request,
    note_id: int,
    body: StickyNoteUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    if body.content is not None:
        note.content = body.content

    if body.status is not None:
        note.status = body.status
        if body.status in (NoteStatus.DONE, NoteStatus.ARCHIVED):
            note.is_help_request = False
            if note.postit_board_id and note.postit_note_id:
                await _notify_postit_archive_async(
                    request, note.postit_board_id, note.postit_note_id
                )

            await db.execute(
                sa_update(BoardPlacement)
                .where(
                    BoardPlacement.note_id == note_id,
                    BoardPlacement.board_type == BoardType.TASK,
                )
                .values(matrix_quadrant=5)
            )
            await db.execute(
                sa_update(BoardPlacement)
                .where(
                    BoardPlacement.note_id == note_id,
                    BoardPlacement.board_type == BoardType.PERSONAL,
                )
                .values(lane=Lane.DONE)
            )
        elif body.status == NoteStatus.ACTIVE:
            from app.routers.board_placements import _restore_task_quadrant

            if note.postit_board_id and note.postit_note_id:
                await _notify_postit_gray_async(
                    request, note.postit_board_id, note.postit_note_id, gray=False
                )

            r_task = await db.execute(
                select(BoardPlacement).where(
                    BoardPlacement.note_id == note_id,
                    BoardPlacement.board_type == BoardType.TASK,
                    BoardPlacement.matrix_quadrant == 5,
                )
            )
            for tp in r_task.scalars().all():
                tp.matrix_quadrant = _restore_task_quadrant(tp)

            await db.execute(
                sa_update(BoardPlacement)
                .where(
                    BoardPlacement.note_id == note_id,
                    BoardPlacement.board_type == BoardType.PERSONAL,
                    BoardPlacement.lane == Lane.DONE,
                )
                .values(lane=Lane.INBOX)
            )

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
        await db.execute(
            sa_update(BoardPlacement)
            .where(BoardPlacement.note_id == note_id)
            .values(is_manually_moved_to_today=False)
        )
        await db.flush()
        await apply_due_date_rules_for_note(note_id, db)
    await db.refresh(note)

    if note.postit_board_id and note.postit_note_id:
        text_to_send = note.content if body.content is not None else None
        due_date_to_send = (
            (note.due_date.isoformat() if note.due_date else "")
            if body.due_date is not None
            else None
        )
        if text_to_send is not None or due_date_to_send is not None:
            await _notify_postit_note_async(
                request,
                note.postit_board_id,
                note.postit_note_id,
                text_to_send,
                due_date_to_send,
            )

    return _note_response(note)


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
        if not note.is_personal_only:
            r_others = await db.execute(
                select(BoardPlacement).where(
                    BoardPlacement.note_id == note.id,
                    BoardPlacement.board_type == BoardType.PERSONAL,
                    BoardPlacement.lane != Lane.DONE,
                )
            )
            if r_others.scalars().first():
                logger.info(
                    "[delete_sticky_notes_by_postit] 未完了担当者が存在するためアーカイブ状態に留めます note_id=%s",
                    note.id,
                )
                note.status = NoteStatus.ARCHIVED
                note.is_help_request = False

                await db.execute(
                    sa_update(BoardPlacement)
                    .where(
                        BoardPlacement.note_id == note.id,
                        BoardPlacement.board_type == BoardType.TASK,
                    )
                    .values(matrix_quadrant=5)
                )
                continue

        await db.delete(note)


@router.delete("/{note_id}", status_code=204)
async def delete_sticky_note(
    request: Request, note_id: int, db: AsyncSession = Depends(get_db)
):
    stmt = select(StickyNote).where(StickyNote.id == note_id)
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if not note:
        return

    if not note.is_personal_only:
        r_others = await db.execute(
            select(BoardPlacement, User)
            .join(User, BoardPlacement.owner_id == User.id)
            .where(
                BoardPlacement.note_id == note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.lane != Lane.DONE,
            )
        )
        others = r_others.all()
        if others:
            names = ", ".join([u.name for p, u in others])
            raise HTTPException(
                status_code=400,
                detail=f"担当者（{names}）が完了にするまで削除できません",
            )

    postit_board_id = note.postit_board_id
    postit_note_id = note.postit_note_id

    if postit_board_id and postit_note_id:
        logger.info(
            "[delete_sticky_note] 付箋ボードへのグレー化通知: board=%s note=%s",
            postit_board_id,
            postit_note_id,
        )
        archived = await _notify_postit_archive_async(
            request, postit_board_id, postit_note_id
        )
        if not archived:
            logger.warning(
                "[delete_sticky_note] グレー化通知に失敗しましたが、タスクボード上の削除を継続します"
            )
        else:
            logger.info("[delete_sticky_note] グレー化通知完了")

    await db.delete(note)
    logger.info("[delete_sticky_note] note_id=%s 削除完了", note_id)


@router.post("/{note_id}/move_to_personal", response_model=BoardPlacementResponse)
async def move_to_personal(
    request: Request,
    note_id: int,
    body: MoveToPersonalBody,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    result = await db.execute(select(User).where(User.id == body.owner_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == body.owner_id,
        )
    )
    placement = result.scalar_one_or_none()

    target_lane = body.lane or Lane.INBOX
    if placement:
        placement.lane = target_lane
    else:
        placement = BoardPlacement(
            note_id=note_id,
            board_type=BoardType.PERSONAL,
            owner_id=body.owner_id,
            lane=target_lane,
            sort_order=0,
        )
        db.add(placement)

    await db.flush()

    await db.execute(
        sa_update(BoardPlacement)
        .where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id != body.owner_id,
            BoardPlacement.lane == Lane.HELP_REQUEST,
        )
        .values(lane=Lane.INBOX)
    )
    await db.flush()

    await _ensure_postit_sync(request, note, db)
    await db.refresh(placement)
    return placement


@router.post("/{note_id}/copy_to_team", response_model=CopyToTeamResponse)
async def copy_to_team(
    request: Request,
    note_id: int,
    body: CopyToTeamBody,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    result = await db.execute(
        select(User).where(User.teams.any(Team.id == body.team_id))
    )
    members = list(result.scalars().all())
    if not members:
        return CopyToTeamResponse(
            created=0,
            user_ids=[],
            message="このチームには所属メンバーがいません",
        )

    copied_count = 0
    user_ids = []
    for member in members:
        res = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.owner_id == member.id,
            )
        )
        existing = res.scalar_one_or_none()
        if not existing:
            placement = BoardPlacement(
                note_id=note_id,
                board_type=BoardType.PERSONAL,
                owner_id=member.id,
                lane=Lane.INBOX,
                sort_order=0,
            )
            db.add(placement)
            copied_count += 1
            user_ids.append(member.id)

    await db.flush()

    await db.execute(
        sa_update(BoardPlacement)
        .where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.lane == Lane.HELP_REQUEST,
        )
        .values(lane=Lane.INBOX)
    )
    await db.flush()

    await _ensure_postit_sync(request, note, db)
    return CopyToTeamResponse(
        created=copied_count,
        user_ids=user_ids,
        message=f"チームメンバー {copied_count} 名の Personal ボードへ追加しました",
    )


@router.post("/{note_id}/release_to_task_board")
async def release_to_task_board(
    request: Request,
    note_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StickyNote).where(StickyNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=404, detail="Sticky note not found")

    note.is_personal_only = False

    r_task = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.note_id == note_id,
            BoardPlacement.board_type == BoardType.TASK,
            BoardPlacement.owner_id.is_(None),
        )
    )
    task_placement = r_task.scalar_one_or_none()
    if not task_placement:
        task_placement = BoardPlacement(
            note_id=note_id,
            board_type=BoardType.TASK,
            owner_id=None,
            matrix_quadrant=1,
            sort_order=0,
            placement_source="personal_release",
        )
        db.add(task_placement)

    await db.flush()

    await _ensure_postit_sync(request, note, db)
    return {"ok": True, "note_id": note_id}
