"""add is_help_request to sticky_notes

Revision ID: n4o5p6q7r8s9
Revises: m3n4o5p6q7r8
Create Date: 2026-10-06

"""
from alembic import op
import sqlalchemy as sa

revision = "n4o5p6q7r8s9"
down_revision = "m3n4o5p6q7r8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sticky_notes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_help_request",
                sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("sticky_notes", schema=None) as batch_op:
        batch_op.drop_column("is_help_request")
