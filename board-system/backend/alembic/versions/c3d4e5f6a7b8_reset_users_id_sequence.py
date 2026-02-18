"""reset users id sequence (シードで明示的 id 投入後も新規ユーザー追加できるようにする)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # シード等で明示的 id を投入していると PostgreSQL の SERIAL シーケンスが進まないため、
    # 新規 INSERT で users_pkey 重複になる。シーケンスを MAX(id) に合わせる。
    op.execute(
        "SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1))"
    )


def downgrade() -> None:
    # リセットの取り消しは不可（冪等に再実行すればよい）
    pass
