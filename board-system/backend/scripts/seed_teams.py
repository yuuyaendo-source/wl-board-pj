# -*- coding: utf-8 -*-
"""
初期チームデータ投入スクリプト。
SEED_TEAMS ("ネットワーク", "構築") を作成し、初期ユーザー (1-8) にチームを割り当てる。
"""
import asyncio
import os
import sys

# app モジュールをインポートできるようにパス追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import async_session_maker, SEED_TEAMS, SEED_USER_TEAM_MAP
from app.models.team import Team
from app.models.user import User


async def seed_teams_async() -> None:
    async with async_session_maker() as session:
        # チームを作成（存在しない場合のみ）
        team_map: dict[str, Team] = {}
        for team_name in SEED_TEAMS:
            r = await session.execute(select(Team).where(Team.name == team_name))
            team = r.scalar_one_or_none()
            if team is None:
                team = Team(name=team_name)
                session.add(team)
                await session.flush()
                print(f"  チーム作成: {team_name} (id={team.id})")
            else:
                print(f"  チーム既存: {team_name} (id={team.id})")
            team_map[team_name] = team
        await session.commit()

        # 初期ユーザーの teams リレーションが空の場合のみ割り当て
        for user_id, team_name in SEED_USER_TEAM_MAP.items():
            r = await session.execute(
                select(User).options(selectinload(User.teams)).where(User.id == user_id)
            )
            user = r.scalar_one_or_none()
            if user is not None and not user.teams:
                target_team = team_map.get(team_name)
                if target_team:
                    user.teams.append(target_team)
                    print(
                        f"  ユーザー {user.name} (id={user.id}) にチーム '{team_name}' を割り当てました"
                    )
        await session.commit()


def main() -> None:
    asyncio.run(seed_teams_async())


if __name__ == "__main__":
    main()
