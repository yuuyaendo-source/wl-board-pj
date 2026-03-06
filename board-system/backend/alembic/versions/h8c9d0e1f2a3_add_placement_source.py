"""add placement_source to board_placements (calendar-origin Today 付箋の識別用)

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-03-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "board_placements",
        sa.Column("placement_source", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("board_placements", "placement_source")
