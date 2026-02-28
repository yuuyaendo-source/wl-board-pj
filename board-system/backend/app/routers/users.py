# -*- coding: utf-8 -*-
from base64 import b64decode
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import BoardPlacement, BoardType, User, UserFace
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        call_name=user.call_name,
        role=user.role,
        face_count=len(user.faces) if user.faces else 0,
    )


@router.get("", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    """ユーザー一覧。共通ユーザー管理・Linko 連携用。"""
    result = await db.execute(
        select(User).options(selectinload(User.faces)).order_by(User.id)
    )
    users = list(result.scalars().unique().all())
    return [_user_to_response(u) for u in users]


@router.get("/by_email", response_model=UserResponse)
async def get_user_by_email(
    email: str = Query(..., description="メールアドレス"),
    db: AsyncSession = Depends(get_db),
):
    """メールでユーザーを1件取得。デスクトップログイン・Linko 解決用。"""
    if not email or not email.strip():
        raise HTTPException(status_code=400, detail="email is required")
    key = email.strip().lower()
    result = await db.execute(
        select(User)
        .options(selectinload(User.faces))
        .where(func.lower(User.email) == key)
        .limit(1)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """ユーザー1件取得。"""
    result = await db.execute(
        select(User).options(selectinload(User.faces)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.post("", response_model=UserResponse)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """ユーザー1件作成。email は一意。"""
    try:
        await db.execute(
            text("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1))")
        )
    except Exception:
        pass  # SQLite では無視
    email_clean = (body.email or "").strip() or None
    if email_clean:
        existing = await db.execute(
            select(User).where(func.lower(User.email) == email_clean.lower())
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="email already registered")
    user = User(
        name=body.name,
        email=email_clean,
        call_name=(body.call_name or "").strip() or None,
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    await db.refresh(user, ["faces"])
    return _user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    """ユーザー1件更新。"""
    result = await db.execute(
        select(User).options(selectinload(User.faces)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.name is not None:
        user.name = body.name
    if body.email is not None:
        email_clean = body.email.strip() or None
        if email_clean:
            other = await db.execute(
                select(User).where(User.id != user_id, func.lower(User.email) == email_clean.lower())
            )
            if other.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="email already registered")
        user.email = email_clean
    if body.call_name is not None:
        user.call_name = body.call_name.strip() or None
    if body.role is not None:
        user.role = body.role
    await db.flush()
    await db.refresh(user)
    return _user_to_response(user)


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


# --- 顔画像 API（複数枚・カメラ/アップロード対応） ---

class FaceListItem(BaseModel):
    id: int
    user_id: int
    source: str | None
    created_at: str

    model_config = {"from_attributes": True}


class AddFaceBody(BaseModel):
    """JSON で base64 画像を送る（カメラ撮影用）。"""
    image: str  # data:image/png;base64,... または base64 のみ
    source: str | None = "camera"


def _decode_image_from_data_url(data_url: str) -> bytes:
    m = re.match(r"data:image/(\w+);base64,(.+)", data_url.strip())
    if m:
        return b64decode(m.group(2))
    return b64decode(data_url)


@router.get("/{user_id}/faces", response_model=list[FaceListItem])
async def list_user_faces(user_id: int, db: AsyncSession = Depends(get_db)):
    """そのユーザーの顔画像一覧（画像本体は含めない）。"""
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")
    faces_result = await db.execute(
        select(UserFace).where(UserFace.user_id == user_id).order_by(UserFace.id)
    )
    faces = list(faces_result.scalars().all())
    return [
        FaceListItem(
            id=f.id,
            user_id=f.user_id,
            source=f.source,
            created_at=f.created_at.isoformat() if f.created_at else "",
        )
        for f in faces
    ]


@router.post("/{user_id}/faces", status_code=201)
async def add_user_face(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """顔画像を1枚追加。Content-Type が application/json のときは body.image (data URL/base64)、multipart のときは file。カメラ・アップロード両対応。"""
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")

    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    image_data: bytes
    src: str = "upload"
    if content_type == "application/json":
        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="invalid JSON")
        img = body.get("image") if isinstance(body, dict) else None
        if not img:
            raise HTTPException(status_code=400, detail="body.image required")
        try:
            image_data = _decode_image_from_data_url(img)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"invalid image data: {e}")
        src = (body.get("source") if isinstance(body, dict) else None) or "camera"
    else:
        form = await request.form()
        file = form.get("file")
        if file is None or not getattr(file, "filename", None):
            raise HTTPException(status_code=400, detail="multipart: file required")
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="empty file")
        src = form.get("source") or "upload"
    face = UserFace(user_id=user_id, image_data=image_data, source=src)
    db.add(face)
    await db.flush()
    return {"id": face.id, "user_id": face.user_id, "source": face.source}


@router.get("/{user_id}/faces/{face_id}/image")
async def get_user_face_image(
    user_id: int,
    face_id: int,
    db: AsyncSession = Depends(get_db),
):
    """1枚の顔画像を返す。"""
    result = await db.execute(
        select(UserFace).where(
            UserFace.id == face_id,
            UserFace.user_id == user_id,
        )
    )
    face = result.scalar_one_or_none()
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    media_type = "image/png"
    if face.image_data[:4] == b"\xff\xd8\xff":
        media_type = "image/jpeg"
    return Response(content=face.image_data, media_type=media_type)


@router.delete("/{user_id}/faces/{face_id}", status_code=204)
async def delete_user_face(
    user_id: int,
    face_id: int,
    db: AsyncSession = Depends(get_db),
):
    """顔画像1枚を削除。"""
    result = await db.execute(
        select(UserFace).where(
            UserFace.id == face_id,
            UserFace.user_id == user_id,
        )
    )
    face = result.scalar_one_or_none()
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    await db.delete(face)
    return None
