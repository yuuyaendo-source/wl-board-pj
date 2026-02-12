# -*- coding: utf-8 -*-
"""4ボード View 用の集約 API。各ボードの配置一覧を付箋本文付きで返す。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote
from app.schemas.board_placement import BoardPlacementWithNoteResponse

router = APIRouter(prefix="/boards", tags=["boards"])


@router.get("/main", response_model=list[BoardPlacementWithNoteResponse])
async def get_board_main(db: AsyncSession = Depends(get_db)):
    """Main Board: 全付箋（MAIN に配置されているもの）。"""
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(BoardPlacement.board_type == BoardType.MAIN)
        .order_by(BoardPlacement.sort_order, BoardPlacement.id)
    )
    rows = result.all()
    return [
        BoardPlacementWithNoteResponse(
            id=p.id,
            note_id=p.note_id,
            board_type=p.board_type,
            owner_id=p.owner_id,
            lane=p.lane,
            position_x=p.position_x,
            position_y=p.position_y,
            matrix_quadrant=p.matrix_quadrant,
            sort_order=p.sort_order,
            note_content=n.content,
            note_status=n.status.value,
        )
        for p, n in rows
    ]


@router.get("/task", response_model=list[BoardPlacementWithNoteResponse])
async def get_board_task(db: AsyncSession = Depends(get_db)):
    """Task Board: 4象限用の配置一覧。"""
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(BoardPlacement.board_type == BoardType.TASK)
        .order_by(BoardPlacement.sort_order, BoardPlacement.id)
    )
    rows = result.all()
    return [
        BoardPlacementWithNoteResponse(
            id=p.id,
            note_id=p.note_id,
            board_type=p.board_type,
            owner_id=p.owner_id,
            lane=p.lane,
            position_x=p.position_x,
            position_y=p.position_y,
            matrix_quadrant=p.matrix_quadrant,
            sort_order=p.sort_order,
            note_content=n.content,
            note_status=n.status.value,
        )
        for p, n in rows
    ]


@router.get("/personal", response_model=list[BoardPlacementWithNoteResponse])
async def get_board_personal(
    owner_id: int = Query(..., description="Personal の所有者"),
    db: AsyncSession = Depends(get_db),
):
    """Personal Board: 指定 owner の INBOX/TODAY/DONE 配置。is_from_task = 当該 note が TASK に存在する。"""
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.board_type == BoardType.PERSONAL,
            BoardPlacement.owner_id == owner_id,
        )
        .order_by(BoardPlacement.lane, BoardPlacement.sort_order, BoardPlacement.id)
    )
    rows = result.all()
    note_ids = [n.id for _, n in rows]
    task_note_ids = set()
    if note_ids:
        r_task = await db.execute(
            select(BoardPlacement.note_id).where(
                BoardPlacement.board_type == BoardType.TASK,
                BoardPlacement.owner_id.is_(None),
                BoardPlacement.note_id.in_(note_ids),
            ).distinct()
        )
        task_note_ids = {row[0] for row in r_task.all()}
    return [
        BoardPlacementWithNoteResponse(
            id=p.id,
            note_id=p.note_id,
            board_type=p.board_type,
            owner_id=p.owner_id,
            lane=p.lane,
            position_x=p.position_x,
            position_y=p.position_y,
            matrix_quadrant=p.matrix_quadrant,
            sort_order=p.sort_order,
            note_content=n.content,
            note_status=n.status.value,
            is_from_task=(n.id in task_note_ids),
        )
        for p, n in rows
    ]


@router.get("/morning", response_model=list[BoardPlacementWithNoteResponse])
async def get_board_morning(db: AsyncSession = Depends(get_db)):
    """Morning Meeting Board: 参加者の Today スナップショット用（現状は MORNING 配置一覧）。"""
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(BoardPlacement.board_type == BoardType.MORNING)
        .order_by(BoardPlacement.sort_order, BoardPlacement.id)
    )
    rows = result.all()
    return [
        BoardPlacementWithNoteResponse(
            id=p.id,
            note_id=p.note_id,
            board_type=p.board_type,
            owner_id=p.owner_id,
            lane=p.lane,
            position_x=p.position_x,
            position_y=p.position_y,
            matrix_quadrant=p.matrix_quadrant,
            sort_order=p.sort_order,
            note_content=n.content,
            note_status=n.status.value,
        )
        for p, n in rows
    ]
