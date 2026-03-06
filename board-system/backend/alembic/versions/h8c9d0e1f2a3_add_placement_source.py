"""add placement_source to board_placements (calendar-origin Today 付箋の識別用)

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-03-06

"""
from typing import Sequence, Union

from alembic import op


revision: str = "h8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 既にカラムがある環境（手動追加や再実行）でもエラーにしない
    op.execute(
        "ALTER TABLE board_placements ADD COLUMN IF NOT EXISTS placement_source VARCHAR(32) NULL"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE board_placements DROP COLUMN IF EXISTS placement_source"
    )
