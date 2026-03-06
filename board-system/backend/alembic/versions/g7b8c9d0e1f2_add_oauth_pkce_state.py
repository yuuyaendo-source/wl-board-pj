"""add oauth_pkce_state for Google OAuth PKCE code_verifier

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 既にテーブルがある環境（手動作成や以前の適用）でもエラーにしない
    op.execute("""
        CREATE TABLE IF NOT EXISTS oauth_pkce_state (
            state VARCHAR(64) NOT NULL,
            code_verifier TEXT NOT NULL,
            expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            PRIMARY KEY (state)
        )
    """)


def downgrade() -> None:
    op.drop_table("oauth_pkce_state")
