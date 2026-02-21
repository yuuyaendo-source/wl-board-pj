# -*- coding: utf-8 -*-
"""
非同期 DB 接続（SQLAlchemy 2.0）。
SQLite (aiosqlite) と PostgreSQL (asyncpg) の両方に対応。
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# DBのURL文字列を取得（Pydanticの型の場合は文字列化）
db_url = str(settings.database_url)

# 接続引数の設定
connect_args = {}
# SQLiteの場合のみ、スレッドチェックを無効化する設定が必要
if "sqlite" in db_url:
    connect_args = {"check_same_thread": False}

# 非同期エンジン作成
engine = create_async_engine(
    db_url,
    connect_args=connect_args, # ここで動的に引数を渡す
    echo=False,  # 開発時は True で SQL ログ出力
)

# 非同期セッション工場
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """全モデルの基底。models ではこれを継承する。"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI の Depends 用。リクエストごとにセッションを発行し、終了時にコミット/ロールバック・クローズ。"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """起動時などにテーブルを作成する（Alembic を使う場合はマイグレーションで実施）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# パーソナルボード用メンバー（id 1-7）。起動時に存在しなければ作成する
PERSONAL_USER_NAMES = [
    "堀 高喜",
    "福山 一道",
    "小林 康三",
    "ブイクエット タン",
    "浅川 久司",
    "遠藤 悠矢",
    "林田 康佑",
]


async def seed_personal_users() -> None:
    """パーソナルボード用ユーザー（id 1-7）がなければ作成する。"""
    # 循環参照を防ぐため関数内でインポート
    from sqlalchemy import select
    from app.models.user import User # ※パスに注意: app.models 直下か app.models.user か確認してください
    
    async with async_session_maker() as session:
        for i, name in enumerate(PERSONAL_USER_NAMES, 1):
            r = await session.execute(select(User).where(User.id == i))
            if r.scalar_one_or_none() is None:
                session.add(User(id=i, name=name))
        await session.commit()