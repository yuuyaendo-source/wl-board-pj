# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models import BoardPlacement, BoardType
from app.schemas.board_placement import (
    BoardPlacementCreate,
    BoardPlacementResponse,
    BoardPlacementUpdate,
)

router = APIRouter(prefix="/board_placements", tags=["board_placements"])


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
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


@router.get("", response_model=list[BoardPlacementResponse])
async def list_board_placements(
    board_type: BoardType | None = Query(None, description="MAIN, TASK, PERSONAL, MORNING"),
    owner_id: int | None = Query(None, description="Personal の場合は必須"),
    db: AsyncSession = Depends(get_db),
):
    """配置一覧。board_type / owner_id でフィルタ。"""
    q = select(BoardPlacement).order_by(BoardPlacement.sort_order, BoardPlacement.id)
    if board_type is not None:
        q = q.where(BoardPlacement.board_type == board_type)
    if owner_id is not None:
        q = q.where(BoardPlacement.owner_id == owner_id)
    result = await db.execute(q)
    return [_placement_response(p) for p in result.scalars().all()]


@router.post("", response_model=BoardPlacementResponse)
async def create_board_placement(body: BoardPlacementCreate, db: AsyncSession = Depends(get_db)):
    """配置1件作成。同一 (note_id, board_type, owner_id) は一意制約のため重複不可。"""
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


@router.get("/{placement_id}", response_model=BoardPlacementResponse)
async def get_board_placement(placement_id: int, db: AsyncSession = Depends(get_db)):
    """配置1件取得。"""
    result = await db.execute(select(BoardPlacement).where(BoardPlacement.id == placement_id))
    placement = result.scalar_one_or_none()
    if not placement:
        raise HTTPException(status_code=404, detail="Board placement not found")
    return _placement_response(placement)


@router.patch("/{placement_id}", response_model=BoardPlacementResponse)
async def update_board_placement(
    placement_id: int,
    body: BoardPlacementUpdate,
    db: AsyncSession = Depends(get_db),
):
    """配置の lane / position_x,y / matrix_quadrant / sort_order を更新。
    1) Personal で DONE にしたらパーソナルにも残しつつ Task を完了(5)に連動。
    2) Task の完了(5)から他列へ移動したら、当該付箋の Personal DONE を INBOX に戻す（グレー→緑）。"""
    result = await db.execute(select(BoardPlacement).where(BoardPlacement.id == placement_id))
    placement = result.scalar_one_or_none()
    if not placement:
        raise HTTPException(status_code=404, detail="Board placement not found")
    prev_lane = placement.lane
    prev_matrix = placement.matrix_quadrant
    if body.lane is not None:
        placement.lane = body.lane
    if body.position_x is not None:
        placement.position_x = body.position_x
    if body.position_y is not None:
        placement.position_y = body.position_y
    if body.matrix_quadrant is not None:
        placement.matrix_quadrant = body.matrix_quadrant
    if body.sort_order is not None:
        placement.sort_order = body.sort_order

    from app.models.board_placement import Lane

    # Personal の DONE ↔ 他レーン変更時に Task の matrix_quadrant（5=完了）を連動
    if placement.board_type == BoardType.PERSONAL and body.lane is not None:
        r_task = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == placement.note_id,
                BoardPlacement.board_type == BoardType.TASK,
                BoardPlacement.owner_id.is_(None),
            )
        )
        task_placement = r_task.scalar_one_or_none()
        if task_placement:
            if body.lane == Lane.DONE:
                task_placement.matrix_quadrant = 5
            elif prev_lane == Lane.DONE and body.lane in (Lane.INBOX, Lane.TODAY):
                task_placement.matrix_quadrant = 4

    # Task の完了(5)から他列へ移動したら、当該付箋の Personal DONE を INBOX に戻す（色がグレー→緑に）
    if (
        placement.board_type == BoardType.TASK
        and body.matrix_quadrant is not None
        and body.matrix_quadrant != 5
        and prev_matrix == 5
    ):
        r_personal = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == placement.note_id,
                BoardPlacement.board_type == BoardType.PERSONAL,
                BoardPlacement.lane == Lane.DONE,
            )
        )
        for p in r_personal.scalars().all():
            p.lane = Lane.INBOX

    await db.flush()
    await db.refresh(placement)
    return _placement_response(placement)


@router.delete("/{placement_id}", status_code=204)
async def delete_board_placement(placement_id: int, db: AsyncSession = Depends(get_db)):
    """配置1件削除（付箋は削除されない）。"""
    result = await db.execute(select(BoardPlacement).where(BoardPlacement.id == placement_id))
    placement = result.scalar_one_or_none()
    if not placement:
        raise HTTPException(status_code=404, detail="Board placement not found")
    await db.delete(placement)
    return None
