"""bind OAuth PKCE state to its user

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-10-20

"""

from alembic import op
import sqlalchemy as sa


revision = "p6q7r8s9t0u1"
down_revision = "o5p6q7r8s9t0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # state は最長10分の一時データ。旧形式（state=user_id）はCSRF保護を満たさないため、
    # 移行時に無効化して新しい認可フローを開始させる。
    op.execute("DELETE FROM oauth_pkce_state")
    with op.batch_alter_table("oauth_pkce_state", schema=None) as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
        batch_op.create_index("ix_oauth_pkce_state_user_id", ["user_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_oauth_pkce_state_user_id_users", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )


def downgrade() -> None:
    with op.batch_alter_table("oauth_pkce_state", schema=None) as batch_op:
        batch_op.drop_constraint("fk_oauth_pkce_state_user_id_users", type_="foreignkey")
        batch_op.drop_index("ix_oauth_pkce_state_user_id")
        batch_op.drop_column("user_id")
