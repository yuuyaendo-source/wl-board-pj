# -*- coding: utf-8 -*-
"""チーム CRUD ルーター。GET /teams / POST /teams / PATCH /teams/{id} / DELETE /teams/{id}。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models.team import Team
from app.models.user import User
from app.schemas.team import TeamCreate, TeamResponse, TeamUpdate

router = APIRouter(prefix="/teams", tags=["teams"])


def _team_to_response(team: Team) -> TeamResponse:
    member_count = len(team.users) if team.users is not None else 0
    return TeamResponse(
        id=team.id,
        name=team.name,
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=member_count,
    )


@router.get("", response_model=list[TeamResponse])
async def list_teams(db: AsyncSession = Depends(get_db)):
    """チーム一覧を取得する。"""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Team).options(selectinload(Team.users)).order_by(Team.id)
    )
    teams = list(result.scalars().unique().all())
    return [_team_to_response(t) for t in teams]


@router.post("", response_model=TeamResponse, status_code=201)
async def create_team(body: TeamCreate, db: AsyncSession = Depends(get_db)):
    """チームを新規作成する。チーム名は一意。"""
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="チーム名は必須です")
    # 同名チームの重複チェック
    existing = await db.execute(select(Team).where(Team.name == name))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="同名のチームが既に存在します")
    team = Team(name=name)
    db.add(team)
    await db.flush()
    await db.refresh(team)
    # ユーザーリレーションを初期化（空リスト）
    team.users = []
    return _team_to_response(team)


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(team_id: int, body: TeamUpdate, db: AsyncSession = Depends(get_db)):
    """チーム名を更新する。"""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Team).options(selectinload(Team.users)).where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="チーム名は必須です")
        # 別チームに同名が存在しないか確認
        other = await db.execute(select(Team).where(Team.name == name, Team.id != team_id))
        if other.scalar_one_or_none() is not None:
            raise HTTPException(status_code=400, detail="同名のチームが既に存在します")
        team.name = name
    await db.flush()
    await db.refresh(team)
    return _team_to_response(team)


@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: int, db: AsyncSession = Depends(get_db)):
    """チームを削除する。所属メンバーの team_id は NULL にクリアされる（ON DELETE SET NULL）。"""
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    # 所属メンバーの team_id を手動で NULL クリア（SQLite は CASCADE ON DELETE が動作しない場合があるため）
    members_result = await db.execute(select(User).where(User.team_id == team_id))
    for user in members_result.scalars().all():
        user.team_id = None
    await db.flush()
    await db.delete(team)
    return None
