# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BoardPlacement, BoardType, User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    """ユーザー一覧。動作確認・開発用。"""
    result = await db.execute(select(User).order_by(User.id))
    return list(result.scalars().all())


@router.post("", response_model=UserResponse)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """ユーザー1件作成。シード等で明示的 id 投入後も動くよう、挿入前に users.id シーケンスを同期する。"""
    await db.execute(
        text("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1))")
    )
    user = User(name=body.name, role=body.role)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """ユーザー1件削除。削除前に当該ユーザーが持つパーソナル付箋をすべてタスクボードへリリース（誰も持っていないタスク＝黄色）する。"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 当該ユーザーの PERSONAL 配置を取得
    placements_result = await db.execute(
        select(BoardPlacement).where(
            BoardPlacement.owner_id == user_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    personal_placements = list(placements_result.scalars().all())

    # 各付箋をタスクボードへリリース（TASK 配置がなければ作成し、PERSONAL 配置を削除）
    for p in personal_placements:
        note_id = p.note_id
        # TASK 配置（owner_id=None＝誰も持っていない）がなければ作成
        task_result = await db.execute(
            select(BoardPlacement).where(
                BoardPlacement.note_id == note_id,
                BoardPlacement.board_type == BoardType.TASK,
                BoardPlacement.owner_id.is_(None),
            ).limit(1)
        )
        if task_result.scalar_one_or_none() is None:
            task_placement = BoardPlacement(
                note_id=note_id,
                board_type=BoardType.TASK,
                owner_id=None,
                sort_order=0,
            )
            db.add(task_placement)
            await db.flush()
        # このユーザーの PERSONAL 配置を削除
        await db.execute(
            delete(BoardPlacement).where(
                BoardPlacement.id == p.id,
            )
        )
    await db.flush()

    await db.delete(user)
    return None
