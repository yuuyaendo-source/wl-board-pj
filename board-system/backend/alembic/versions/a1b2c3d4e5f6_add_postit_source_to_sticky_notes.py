"""add postit_source to sticky_notes

Revision ID: a1b2c3d4e5f6
Revises: 18f12e452b24
Create Date: 2026-02-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "18f12e452b24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sticky_notes", sa.Column("postit_board_id", sa.String(64), nullable=True))
    op.add_column("sticky_notes", sa.Column("postit_note_id", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("sticky_notes", "postit_note_id")
    op.drop_column("sticky_notes", "postit_board_id")
