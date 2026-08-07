#!/usr/bin/env python3
"""
チーム（ネットワーク/構築）を本番DBに登録し、既存ユーザー（id 1-7）に初期割り当てを行う。
既にチームが存在する場合はスキップ。ユーザーの team_id が NULL の場合のみ割り当て。

使い方（ホストで実行する場合）:
  cd /var/www/wlinko-pj/board-system/backend
  source .venv/bin/activate
  DATABASE_URL="postgresql://linko_user:linko_password@127.0.0.1:5433/linko_board_system" python scripts/seed_teams.py

Docker コンテナ内:
  docker exec -it linko-backend-blue python scripts/seed_teams.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SEED_TEAMS = ["ネットワーク", "構築"]

# 奇数ID → ネットワーク, 偶数ID → 構築
SEED_USER_TEAM_MAP: dict[int, str] = {
    1: "ネットワーク",
    2: "構築",
    3: "ネットワーク",
    4: "構築",
    5: "ネットワーク",
    6: "構築",
    7: "ネットワーク",
}


def main() -> None:
    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        print("DATABASE_URL を設定してください", file=sys.stderr)
        sys.exit(1)
    pg_url = pg_url.replace("postgresql+asyncpg", "postgresql", 1).replace("postgresql+psycopg2", "postgresql", 1)

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    from app.models import Team, User

    engine = create_engine(pg_url)
    session_factory = sessionmaker(engine, autocommit=False, autoflush=False)

    with session_factory() as db:
        # チーム作成（存在しない場合のみ）
        team_map: dict[str, int] = {}
        teams_added = 0
        for team_name in SEED_TEAMS:
            team = db.query(Team).filter(Team.name == team_name).first()
            if team is None:
                team = Team(name=team_name)
                db.add(team)
                db.flush()
                teams_added += 1
                print(f"  チーム追加: {team_name}")
            else:
                print(f"  チーム既存: {team_name} (id={team.id})")
            team_map[team_name] = team.id
        db.commit()

        # シーケンス更新（PostgreSQL）
        if teams_added > 0:
            try:
                db.execute(text(
                    "SELECT setval(pg_get_serial_sequence('teams', 'id'), (SELECT COALESCE(MAX(id), 1) FROM teams))"
                ))
                db.commit()
            except Exception:
                pass

        # ユーザーへのチーム割り当て（team_id が NULL の場合のみ）
        assigned = 0
        for user_id, team_name in SEED_USER_TEAM_MAP.items():
            user = db.get(User, user_id)
            if user is not None and user.team_id is None:
                user.team_id = team_map.get(team_name)
                assigned += 1
                print(f"  ユーザー割り当て: id={user_id}, name={user.name} → {team_name}")
        db.commit()

        print(f"\nチーム: {teams_added} 件追加しました。")
        print(f"ユーザー割り当て: {assigned} 件設定しました。")


if __name__ == "__main__":
    main()
