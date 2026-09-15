"""add is_personal_only to sticky_notes

Revision ID: m3n4o5p6q7r8
Revises: l2m3n4o5p6q7
Create Date: 2026-09-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "m3n4o5p6q7r8"
down_revision: Union[str, Sequence[str], None] = "l2m3n4o5p6q7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("sticky_notes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_personal_only",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("sticky_notes", schema=None) as batch_op:
        batch_op.drop_column("is_personal_only")
