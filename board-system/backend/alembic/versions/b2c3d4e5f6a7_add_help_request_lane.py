"""add HELP_REQUEST to lane (応援要請)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # lane に HELP_REQUEST（応援要請）を追加。native_enum=False のため実体は文字列で、長さを確保
    with op.batch_alter_table("board_placements", schema=None) as batch_op:
        batch_op.alter_column(
            "lane",
            type_=sa.String(length=20),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("board_placements", schema=None) as batch_op:
        batch_op.alter_column(
            "lane",
            type_=sa.Enum("INBOX", "TODAY", "DONE", name="lane", native_enum=False),
            existing_nullable=True,
        )
