# -*- coding: utf-8 -*-
from base64 import b64decode
import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import BoardPlacement, BoardType, StickyNote, User, UserFace, Team
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.routers.auth_admin import get_current_admin
from app.services.calendar_placement import CALENDAR_PLACEMENT_SOURCES

router = APIRouter(prefix="/users", tags=["users"])


def _user_to_response(user: User) -> UserResponse:
    teams_list = user.teams if hasattr(user, "teams") and user.teams is not None else []
    team_ids = [t.id for t in teams_list]
    teams_summary = [{"id": t.id, "name": t.name} for t in teams_list]

    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        call_name=user.call_name,
        role=user.role,
        team_ids=team_ids,
        teams=teams_summary,
        face_count=len(user.faces) if hasattr(user, "faces") and user.faces else 0,
    )


@router.get("", response_model=list[UserResponse])
async def list_users(db: AsyncSession = Depends(get_db)):
    """ユーザー一覧。共通ユーザー管理・Linko 連携用。"""
    result = await db.execute(
        select(User)
        .options(selectinload(User.faces), selectinload(User.teams))
        .order_by(User.id)
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
        .options(selectinload(User.faces), selectinload(User.teams))
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
        select(User)
        .options(selectinload(User.faces), selectinload(User.teams))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_response(user)


@router.post("", response_model=UserResponse)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """ユーザー1件作成。email は一意。管理者権限が必要。"""
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

    if body.team_ids:
        r = await db.execute(select(Team).where(Team.id.in_(body.team_ids)))
        user.teams = list(r.scalars().all())
    else:
        user.teams = []

    db.add(user)
    await db.flush()
    await db.refresh(user, ["faces", "teams"])
    return _user_to_response(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """ユーザー1件更新。管理者権限が必要。"""
    result = await db.execute(
        select(User)
        .options(selectinload(User.faces), selectinload(User.teams))
        .where(User.id == user_id)
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
                select(User).where(
                    User.id != user_id, func.lower(User.email) == email_clean.lower()
                )
            )
            if other.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="email already registered")
        user.email = email_clean
    if body.call_name is not None:
        user.call_name = body.call_name.strip() or None
    if body.role is not None:
        user.role = body.role

    if body.team_ids is not None:
        if body.team_ids:
            r = await db.execute(select(Team).where(Team.id.in_(body.team_ids)))
            user.teams = list(r.scalars().all())
        else:
            user.teams = []

    await db.flush()
    await db.refresh(user, ["faces", "teams"])
    return _user_to_response(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: str = Depends(get_current_admin),
):
    """ユーザー1件削除。削除前に当該ユーザーが持つパーソナル付箋をタスクボードへリリース（個人専用メモ・カレンダー付箋を除く）。管理者権限が必要。"""
    result = await db.execute(
        select(User).options(selectinload(User.teams)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    placements_result = await db.execute(
        select(BoardPlacement, StickyNote)
        .join(StickyNote, BoardPlacement.note_id == StickyNote.id)
        .where(
            BoardPlacement.owner_id == user_id,
            BoardPlacement.board_type == BoardType.PERSONAL,
        )
    )
    personal_rows = list(placements_result.all())

    for p, note in personal_rows:
        note_id = p.note_id
        is_calendar = getattr(p, "placement_source", None) in CALENDAR_PLACEMENT_SOURCES

        if not note.is_personal_only and not is_calendar:
            task_result = await db.execute(
                select(BoardPlacement)
                .where(
                    BoardPlacement.note_id == note_id,
                    BoardPlacement.board_type == BoardType.TASK,
                    BoardPlacement.owner_id.is_(None),
                )
                .limit(1)
            )
            if task_result.scalar_one_or_none() is None:
                task_placement = BoardPlacement(
                    note_id=note_id,
                    board_type=BoardType.TASK,
                    owner_id=None,
                    matrix_quadrant=1,
                    sort_order=0,
                )
                db.add(task_placement)
                await db.flush()

        await db.execute(
            delete(BoardPlacement).where(
                BoardPlacement.id == p.id,
            )
        )
        await db.flush()

        if note.is_personal_only or is_calendar:
            other_placements = await db.execute(
                select(BoardPlacement.id)
                .where(BoardPlacement.note_id == note_id)
                .limit(1)
            )
            if other_placements.scalar_one_or_none() is None:
                await db.delete(note)

    user.teams = []
    await db.flush()
    await db.delete(user)
    return None


class FaceListItem(BaseModel):
    id: int
    user_id: int
    source: str | None
    created_at: str

    model_config = {"from_attributes": True}


class AddFaceBody(BaseModel):
    """JSON で base64 画像を送る（カメラ撮影用）。"""

    image: str
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
    result = await db.execute(select(User).where(User.id == user_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="User not found")

    content_type = (
        (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    )
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
