"""add system_settings for runtime LLM slot override

Revision ID: i9j0k1l2m3n4
Revises: h8c9d0e1f2a3
Create Date: 2026-03-30

"""
from typing import Sequence, Union

from alembic import op


revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, Sequence[str], None] = "h8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS system_settings (
            id INTEGER NOT NULL PRIMARY KEY,
            llm_target INTEGER NULL
        )
        """
    )
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "INSERT INTO system_settings (id, llm_target) VALUES (1, NULL) "
            "ON CONFLICT (id) DO NOTHING"
        )
    else:
        op.execute(
            "INSERT OR IGNORE INTO system_settings (id, llm_target) VALUES (1, NULL)"
        )


def downgrade() -> None:
    op.drop_table("system_settings")
