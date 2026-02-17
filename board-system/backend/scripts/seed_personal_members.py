#!/usr/bin/env python3
"""
パーソナルボード用のユーザー（id 1〜7）を登録する。フロントの PERSONAL_MEMBERS と対応。
新サーバで DB を空の状態で立ち上げた場合、パーソナルボードで投稿するにはこのスクリプトか
移行スクリプトで users を用意する必要がある。

使い方:
  DATABASE_URL=postgresql+asyncpg://linko_user:linko_password@127.0.0.1:5433/linko_board_system python scripts/seed_personal_members.py

または Docker コンテナ内:
  docker exec -it linko-backend-blue python scripts/seed_personal_members.py
  （コンテナ内の DATABASE_URL がそのまま使われる）
"""
import asyncio
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


async def main() -> None:
    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        print("DATABASE_URL を設定してください", file=sys.stderr)
        sys.exit(1)
    if "postgresql+asyncpg" not in pg_url:
        print("postgresql+asyncpg の URL を指定してください（例: postgresql+asyncpg://...）", file=sys.stderr)
        sys.exit(1)

    from sqlalchemy import select, text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app.models import User

    engine = create_async_engine(pg_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        added = 0
        for user_id, name in PERSONAL_MEMBERS:
            r = await db.execute(select(User).where(User.id == user_id))
            if r.scalar_one_or_none() is not None:
                continue
            db.add(User(id=user_id, name=name))
            added += 1
            print(f"  追加: id={user_id}, name={name}")
        await db.commit()
        if added > 0:
            # 次回の INSERT で id が重複しないようシーケンスを更新
            await db.execute(text(
                "SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT COALESCE(MAX(id), 1) FROM users))"
            ))
            await db.commit()
        print(f"users: {added} 件追加しました。" if added else "users: 変更なし（既に 1〜7 が存在します）。")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
