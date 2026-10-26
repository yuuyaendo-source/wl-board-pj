"""add due_date to sticky_notes and is_manually_moved_to_today to board_placements

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-08-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "k1l2m3n4o5p6"
down_revision: Union[str, Sequence[str], None] = "j0k1l2m3n4o5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # sticky_notes に due_date カラムを追加
    with op.batch_alter_table("sticky_notes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("due_date", sa.Date(), nullable=True))

    # board_placements に is_manually_moved_to_today カラムを追加
    with op.batch_alter_table("board_placements", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_manually_moved_to_today",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("board_placements", schema=None) as batch_op:
        batch_op.drop_column("is_manually_moved_to_today")

    with op.batch_alter_table("sticky_notes", schema=None) as batch_op:
        batch_op.drop_column("due_date")
