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
    taken_by_map: dict[int, list[tuple[int, str, str, bool]]] = {}
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

            is_done = lane == Lane.DONE
            # 既存のリスト内に同じユーザーが登録されていなければ追加
            existing = next(
                (x for x in taken_by_map[note_id] if x[0] == owner_id), None
            )
            if not existing:
                taken_by_map[note_id].append(
                    (owner_id, u.name, _name_short(u.name), is_done)
                )
            else:
                # 複数配置がある場合、一つでもDONEならTrueとして上書き
                if is_done and not existing[3]:
                    taken_by_map[note_id].remove(existing)
                    taken_by_map[note_id].append(
                        (owner_id, u.name, _name_short(u.name), True)
                    )

            if lane == Lane.HELP_REQUEST:
                help_request_note_ids.add(note_id)
            else:
                accepted_by_others_note_ids.add(note_id)

    out = []
    for p, n in rows:
        taken = taken_by_map.get(n.id, [])
        taken_by = [
            TakenByUser(id=uid, name=name, name_short=short, is_done=is_done)
            for uid, name, short, is_done in taken
        ]
        is_help = getattr(n, "is_help_request", False) or (
            n.id in help_request_note_ids
        )
        is_completed = (p.matrix_quadrant == 5) or (
            len(taken) > 0 and all(t.is_done for t in taken_by)
        )

        if is_completed:
            task_color = "grey"
        elif is_help:
            task_color = "red"
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
                is_help_request=is_help,
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
    taken_by_map: dict[int, list[TakenByUser]] = {}

    if note_ids:
        # 1. Taskボードに存在するか判定
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

        # 2. 他メンバーの配置情報から taken_by リストを組み立て
        personal_result = await db.execute(
            select(
                BoardPlacement.note_id, BoardPlacement.owner_id, BoardPlacement.lane
            ).where(
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.note_id.in_(note_ids),
                BoardPlacement.owner_id != owner_id,
                BoardPlacement.owner_id.isnot(None),
            )
        )
        personal_rows = personal_result.all()
        other_owner_ids = {r[1] for r in personal_rows}
        users_dict = {}
        if other_owner_ids:
            users_result = await db.execute(
                select(User).where(User.id.in_(other_owner_ids))
            )
            users_dict = {u.id: u for u in users_result.scalars().all()}

        for nid, oid, lane in personal_rows:
            u = users_dict.get(oid)
            if not u:
                continue
            if nid not in taken_by_map:
                taken_by_map[nid] = []

            is_done = lane == Lane.DONE
            # 同一人物の重複を排除しつつ、is_doneフラグを更新
            existing = next((x for x in taken_by_map[nid] if x.id == oid), None)
            if not existing:
                taken_by_map[nid].append(
                    TakenByUser(
                        id=oid,
                        name=u.name,
                        name_short=_name_short(u.name),
                        is_done=is_done,
                    )
                )
            else:
                if is_done and not existing.is_done:
                    existing.is_done = True

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
            is_help_request=getattr(n, "is_help_request", False),
            taken_by=taken_by_map.get(n.id, []),
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
            is_help_request=getattr(n, "is_help_request", False),
        )
        for p, n in rows
    ]
