#!/usr/bin/env python3
"""
パーソナルボード用のユーザー（id 1〜7）を登録する。フロントの PERSONAL_MEMBERS と対応。
新サーバで DB を空の状態で立ち上げた場合、パーソナルボードで投稿するにはこのスクリプトか
移行スクリプトで users を用意する必要がある。

使い方（ホストで実行する場合）:
  cd /var/www/wlinko-pj/board-system/backend
  source .venv/bin/activate
  DATABASE_URL="postgresql://linko_user:linko_password@127.0.0.1:5433/linko_board_system" python scripts/seed_personal_members.py

Docker コンテナ内（イメージに scripts が含まれるように再ビルド済みの場合）:
  docker exec -it linko-backend-blue python scripts/seed_personal_members.py
"""
import os
import sys

# backend をパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# フロントの personalMembers と id を揃える（slug は未使用・名前のみ）
PERSONAL_MEMBERS = [
    (1, "堀 高喜"),
    (2, "福山 一道"),
    (3, "小林 康三"),
    (4, "ブイクエット タン"),
    (5, "浅川 久司"),
    (6, "遠藤 悠矢"),
    (7, "林田 康佑"),
]


def main() -> None:
    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        print("DATABASE_URL を設定してください", file=sys.stderr)
        sys.exit(1)
    # psycopg2 用に postgresql:// に統一（+asyncpg / +psycopg2 は外す）
    pg_url = pg_url.replace("postgresql+asyncpg", "postgresql", 1).replace("postgresql+psycopg2", "postgresql", 1)

    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session, sessionmaker

    from app.models import User

    engine = create_engine(pg_url)
    session_factory = sessionmaker(engine, autocommit=False, autoflush=False)

    with session_factory() as db:
        added = 0
        for user_id, name in PERSONAL_MEMBERS:
            if db.get(User, user_id) is not None:
                continue
            db.add(User(id=user_id, name=name))
            added += 1
            print(f"  追加: id={user_id}, name={name}")
        db.commit()
        if added > 0:
            db.execute(text(
                "SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT COALESCE(MAX(id), 1) FROM users))"
            ))
            db.commit()
        print(f"users: {added} 件追加しました。" if added else "users: 変更なし（既に 1〜7 が存在します）。")


if __name__ == "__main__":
    main()
