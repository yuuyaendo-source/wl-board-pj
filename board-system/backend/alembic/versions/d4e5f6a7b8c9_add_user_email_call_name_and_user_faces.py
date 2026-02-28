"""add user email call_name and user_faces table (common user management)

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users に email, call_name を追加
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("email", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("call_name", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_users_email", ["email"], unique=True)

    # user_faces テーブル作成
    op.create_table(
        "user_faces",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_faces_user_id", "user_faces", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_faces_user_id", table_name="user_faces")
    op.drop_table("user_faces")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_email")
        batch_op.drop_column("call_name")
        batch_op.drop_column("email")
