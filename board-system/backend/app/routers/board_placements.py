# -*- coding: utf-8 -*-
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.models.sticky_note import NoteStatus
from app.schemas.board_placement import (
    BoardPlacementCreate,
    BoardPlacementResponse,
    BoardPlacementUpdate,
    ReorderPersonalLaneBody,
)
from app.routers.sticky_notes import _notify_postit_archive_async
from app.services.calendar_placement import CALENDAR_PLACEMENT_SOURCES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/board_placements", tags=["board_placements"])


def _restore_task_quadrant(task_placement: BoardPlacement) -> int:
    """Task 配置の position_x, position_y (AI スコア) から本来の象限 (1-4) を再計算。デフォルトは 1 (アイデア)。"""
    x = task_placement.position_x
    y = task_placement.position_y
    if x is not None and y is not None:
        if x >= 50 and y >= 50:
            return 4
        elif x < 50 and y >= 50:
            return 3
        elif x >= 50 and y < 50:
            return 2
        else:
            return 1
    return 1


async def _notify_postit_gray_async(
    request: Request, board_id: str, note_id: str, gray: bool
) -> bool:
    """付箋ボードへグレーアウト状態の変更（True / False）を非同期通知する。"""
    url = (
        f"{settings.postit_board_url.rstrip('/')}/api/boards/{board_id}/notes/{note_id}"
    )
    try:
        client = request.app.state.http_client
        resp = await client.patch(url, json={"gray": gray}, timeout=5.0)
        return 200 <= resp.status_code < 300
    except Exception as e:
        logger.warning("付箋ボードグレー状態(%s)更新通知失敗: %s", gray, e)
        return False


def _placement_response(p: BoardPlacement) -> BoardPlacementResponse:
    return BoardPlacementResponse(
        id=p.id,
        note_id=p.note_id,
        board_type=p.board_type,
        owner_id=p.owner_id,
        lane=p.lane,
        position_x=p.position_x,
        position_y=p.position_y,
        matrix_quadrant=p.matrix_quadrant,
        sort_order=p.sort_order,
        placement_source=getattr(p, "placement_source", None),
        is_manually_moved_to_today=p.is_manually_moved_to_today,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=list[BoardPlacementResponse])
async def list_board_placements(
    board_type: BoardType | None = Query(None, description="TASK, PERSONAL, MORNING"),
    owner_id: int | None = Query(None, description="Personal の場合は必須"),
    db: AsyncSession = Depends(get_db),
):
    valid_board_types = [BoardType.TASK, BoardType.PERSONAL, BoardType.MORNING]
    q = (
        select(BoardPlacement)
        .where(BoardPlacement.board_type.in_(valid_board_types))
        .order_by(BoardPlacement.sort_order, BoardPlacement.id)
    )
    if board_type is not None:
        q = q.where(BoardPlacement.board_type == board_type)
    if owner_id is not None:
        q = q.where(BoardPlacement.owner_id == owner_id)
    result = await db.execute(q)
    return [_placement_response(p) for p in result.scalars().all()]


@router.post("", response_model=BoardPlacementResponse)
async def create_board_placement(
    body: BoardPlacementCreate, db: AsyncSession = Depends(get_db)
):
    placement = BoardPlacement(
        note_id=body.note_id,
        board_type=body.board_type,
        owner_id=body.owner_id,
        lane=body.lane,
        position_x=body.position_x,
        position_y=body.position_y,
        sort_order=body.sort_order,
    )
    db.add(placement)
    await db.flush()
    await db.refresh(placement)
    return _placement_response(placement)


@router.post("/reorder_personal_lane", status_code=200)
async def reorder_personal_lane(
    body: ReorderPersonalLaneBody,
    db: AsyncSession = Depends(get_db),
):
    if not body.placement_ids:
        return {"ok": True}
    result = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.id.in_(body.placement_ids),
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == body.owner_id,
            BoardPlacement.lane == body.lane,
        )
    )
    placements = {p.id: p for p in result.scalars().all()}
    for order, pid in enumerate(body.placement_ids):
        if pid in placements:
            placements[pid].sort_order = order
    await db.flush()
    return {"ok": True}


@router.get("/{placement_id}", response_model=BoardPlacementResponse)
async def get_board_placement(placement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BoardPlacement).where(BoardPlacement.id == placement_id)
    )
    placement = result.scalar_one_or_none()
    if not placement:
        raise HTTPException(status_code=404, detail="Board placement not found")
    return _placement_response(placement)


@router.patch("/{placement_id}", response_model=BoardPlacementResponse)
async def update_board_placement(
    request: Request,
    placement_id: int,
    body: BoardPlacementUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BoardPlacement).where(BoardPlacement.id == placement_id)
    )
    placement = result.scalar_one_or_none()
    if not placement:
        raise HTTPException(status_code=404, detail="Board placement not found")
    prev_lane = placement.lane
    prev_matrix = placement.matrix_quadrant
    if body.lane is not None:
        placement.lane = body.lane
        if placement.board_type == BoardType.PERSONAL:
            if body.lane == Lane.TODAY:
                placement.is_manually_moved_to_today = True
            else:
                placement.is_manually_moved_to_today = False
    if body.position_x is not None:
        placement.position_x = body.position_x
    if body.position_y is not None:
        placement.position_y = body.position_y
    if body.matrix_quadrant is not None:
        placement.matrix_quadrant = body.matrix_quadrant
    if body.sort_order is not None:
        placement.sort_order = body.sort_order

    note_result = await db.execute(
        select(StickyNote).where(StickyNote.id == placement.note_id)
    )
    note = note_result.scalar_one_or_none()

    if placement.board_type == BoardType.PERSONAL and body.lane is not None:
        if body.lane == Lane.HELP_REQUEST:
            if note:
                note.is_help_request = True
                note.is_personal_only = False
        elif prev_lane == Lane.HELP_REQUEST:
            r_other_help = await db.execute(
                select(BoardPlacement).where(
                    BoardPlacement.note_id == placement.note_id,
                    BoardPlacement.board_type == BoardType.PERSONAL,
                    BoardPlacement.id != placement.id,
                    BoardPlacement.lane == Lane.HELP_REQUEST,
                )
            )
            if not r_other_help.scalars().first() and note:
                note.is_help_request = False

        r_task = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == placement.note_id,
                BoardPlacement.board_type == BoardType.TASK,
                BoardPlacement.owner_id.is_(None),
            )
        )
        task_placement = r_task.scalar_one_or_none()
        if body.lane == Lane.HELP_REQUEST and not task_placement:
            task_placement = BoardPlacement(
                note_id=placement.note_id,
                board_type=BoardType.TASK,
                owner_id=None,
                matrix_quadrant=1,
                sort_order=0,
            )
            db.add(task_placement)
            await db.flush()

        if task_placement:
            if body.lane == Lane.DONE:
                r_other_personal = await db.execute(
                    select(BoardPlacement.lane).where(
                        BoardPlacement.note_id == placement.note_id,
                        BoardPlacement.board_type == BoardType.PERSONAL,
                        BoardPlacement.id != placement.id,
                    )
                )
                other_lanes = r_other_personal.scalars().all()
                all_others_done = all(l == Lane.DONE for l in other_lanes)

                if all_others_done:
                    task_placement.matrix_quadrant = 5
                    if note:
                        note.status = NoteStatus.DONE
                        note.is_help_request = False
                        if note.postit_board_id and note.postit_note_id:
                            await _notify_postit_archive_async(
                                request, note.postit_board_id, note.postit_note_id
                            )
            elif prev_lane == Lane.DONE and body.lane in (
                Lane.INBOX,
                Lane.TODAY,
                Lane.HELP_REQUEST,
            ):
                if task_placement.matrix_quadrant == 5:
                    task_placement.matrix_quadrant = _restore_task_quadrant(
                        task_placement
                    )
                if note:
                    note.status = NoteStatus.ACTIVE

    if placement.board_type == BoardType.TASK and body.matrix_quadrant is not None:
        if body.matrix_quadrant == 5:
            if note:
                note.status = NoteStatus.DONE
                note.is_help_request = False
                if note.postit_board_id and note.postit_note_id:
                    await _notify_postit_archive_async(
                        request, note.postit_board_id, note.postit_note_id
                    )
            await db.execute(
                sa_update(BoardPlacement)
                .where(
                    BoardPlacement.note_id == placement.note_id,
                    BoardPlacement.board_type == BoardType.PERSONAL,
                )
                .values(lane=Lane.DONE)
            )
        elif prev_matrix == 5 and body.matrix_quadrant != 5:
            if note:
                note.status = NoteStatus.ACTIVE
                # ⑧ 完了列からの復帰時に付箋ボード側のグレーアウト（完了状態）を解除通知
                if note.postit_board_id and note.postit_note_id:
                    await _notify_postit_gray_async(
                        request, note.postit_board_id, note.postit_note_id, gray=False
                    )
            r_personal = await db.execute(
                select(BoardPlacement).where(
                    BoardPlacement.note_id == placement.note_id,
                    BoardPlacement.board_type == BoardType.PERSONAL,
                    BoardPlacement.lane == Lane.DONE,
                )
            )
            # 完了列からの復帰時に is_manually_moved_to_today も False にリセット
            for p in r_personal.scalars().all():
                p.lane = Lane.INBOX
                p.is_manually_moved_to_today = False

    await db.flush()
    await db.refresh(placement)
    return _placement_response(placement)


@router.delete("/{placement_id}", status_code=204)
async def delete_board_placement(placement_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BoardPlacement).where(BoardPlacement.id == placement_id)
    )
    placement = result.scalar_one_or_none()
    if not placement:
        raise HTTPException(status_code=404, detail="Board placement not found")

    note_id = placement.note_id
    stmt = select(StickyNote).where(StickyNote.id == note_id)
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    r_note = await db.execute(stmt)
    note = r_note.scalar_one_or_none()

    if placement.board_type == BoardType.PERSONAL:
        r_other_personal = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.id != placement.id,
            )
        )
        other_placements = r_other_personal.scalars().all()

        r_task = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == note_id,
                BoardPlacement.board_type == BoardType.TASK,
                BoardPlacement.owner_id.is_(None),
            )
        )
        task_placement = r_task.scalar_one_or_none()

        if task_placement:
            # ① 他に担当者が残っている場合にのみ完了/未完了の再評価を行い、単独所有タスク削除時の誤復活を防止
            if other_placements:
                if all(p.lane == Lane.DONE for p in other_placements):
                    task_placement.matrix_quadrant = 5
                    if note:
                        note.status = NoteStatus.DONE
                        note.is_help_request = False
                else:
                    if task_placement.matrix_quadrant == 5:
                        task_placement.matrix_quadrant = _restore_task_quadrant(
                            task_placement
                        )
                    if note and note.status == NoteStatus.DONE:
                        note.status = NoteStatus.ACTIVE

    elif placement.board_type == BoardType.TASK:
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

    is_personal_only = getattr(note, "is_personal_only", False) if note else False
    is_calendar = (
        getattr(placement, "placement_source", None) in CALENDAR_PLACEMENT_SOURCES
    )

    await db.delete(placement)
    await db.flush()

    # パーソナル専用・カレンダー由来付箋、または他に配置が存在しない付箋本体を削除
    if note and (is_personal_only or is_calendar):
        r_remaining = await db.execute(
            select(BoardPlacement.id).where(BoardPlacement.note_id == note_id).limit(1)
        )
        if r_remaining.scalar_one_or_none() is None:
            await db.delete(note)

    return None
