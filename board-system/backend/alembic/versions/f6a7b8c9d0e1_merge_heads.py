"""merge heads: reset_users_id_sequence and user_google_tokens

Revision ID: f6a7b8c9d0e1
Revises: c3d4e5f6a7b8, e5f6a7b8c9d0
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = ("c3d4e5f6a7b8", "e5f6a7b8c9d0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # マージのみ。スキーマ変更なし。
    pass


def downgrade() -> None:
    pass
