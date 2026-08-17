# -*- coding: utf-8 -*-
"""4ボード View 用の集約 API。各ボードの配置一覧を付箋本文付きで返す。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User
from app.models.board_placement import Lane
from app.schemas.board_placement import BoardPlacementWithNoteResponse, TakenByUser

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
            due_date=n.due_date.isoformat() if n.due_date else None,
        )
        for p, n in rows
    ]


def _name_short(name: str) -> str:
    """表示用短縮名（例: 浅川久司 → 浅）。"""
    if not name or not name.strip():
        return "?"
    return name.strip()[0]


@router.get("/task", response_model=list[BoardPlacementWithNoteResponse])
async def get_board_task(db: AsyncSession = Depends(get_db)):
    """Task Board: 5列（アイデア・短期・長期・重要・完了）＋ 引き取り者・色。"""
    result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(BoardPlacement.board_type == BoardType.TASK)
        .order_by(BoardPlacement.sort_order, BoardPlacement.id)
    )
    rows = result.all()
    note_ids = [n.id for _, n in rows]
    taken_by_map: dict[int, list[tuple[int, str, str]]] = {}
    done_note_ids: set[int] = set()
    help_request_note_ids: set[int] = set()
    accepted_by_others_note_ids: set[int] = set()
    if note_ids:
        personal_result = await db.execute(
            select(
                BoardPlacement.note_id, BoardPlacement.owner_id, BoardPlacement.lane
            ).where(
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.note_id.in_(note_ids),
                BoardPlacement.owner_id.isnot(None),
            )
        )
        personal_rows = personal_result.all()
        owner_ids = {r[1] for r in personal_rows if r[1] is not None}
        users_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
        users = {u.id: u for u in users_result.scalars().all()}
        for note_id, owner_id, lane in personal_rows:
            if owner_id is None:
                continue
            u = users.get(owner_id)
            if not u:
                continue
            if note_id not in taken_by_map:
                taken_by_map[note_id] = []
            if (owner_id, u.name, _name_short(u.name)) not in [
                (x[0], x[1], x[2]) for x in taken_by_map[note_id]
            ]:
                taken_by_map[note_id].append((owner_id, u.name, _name_short(u.name)))
            if lane == Lane.DONE:
                done_note_ids.add(note_id)
            if lane == Lane.HELP_REQUEST:
                help_request_note_ids.add(note_id)
            else:
                accepted_by_others_note_ids.add(note_id)
    out = []
    for p, n in rows:
        taken = taken_by_map.get(n.id, [])
        taken_by = [
            TakenByUser(id=uid, name=name, name_short=short)
            for uid, name, short in taken
        ]
        if n.id in help_request_note_ids:
            task_color = "red"
        elif n.id in done_note_ids or (
            p.matrix_quadrant is not None and p.matrix_quadrant == 5
        ):
            task_color = "grey"
        elif taken:
            task_color = "green"
        else:
            task_color = "yellow"
        out.append(
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
                taken_by=taken_by,
                task_color=task_color,
                is_accepted_by_others=n.id in accepted_by_others_note_ids,
                due_date=n.due_date.isoformat() if n.due_date else None,
            )
        )
    return out


@router.get("/personal", response_model=list[BoardPlacementWithNoteResponse])
async def get_board_personal(
    owner_id: int = Query(..., description="Personal の所有者"),
    db: AsyncSession = Depends(get_db),
):
    """Personal Board: 指定 owner の INBOX/TODAY/DONE 配置。"""
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
            select(BoardPlacement.note_id)
            .where(
                BoardPlacement.board_type == BoardType.TASK,
                BoardPlacement.owner_id.is_(None),
                BoardPlacement.note_id.in_(note_ids),
            )
            .distinct()
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
            placement_source=p.placement_source,
            is_from_task=(n.id in task_note_ids),
            is_manually_moved_to_today=p.is_manually_moved_to_today,
            due_date=n.due_date.isoformat() if n.due_date else None,
        )
        for p, n in rows
    ]


@router.get("/morning", response_model=list[BoardPlacementWithNoteResponse])
async def get_board_morning(db: AsyncSession = Depends(get_db)):
    """Morning Meeting Board"""
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
            placement_source=p.placement_source,
            due_date=n.due_date.isoformat() if n.due_date else None,
        )
        for p, n in rows
    ]
