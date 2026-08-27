"""add user_teams and admin auth

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-08-27

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "l2m3n4o5p6q7"
down_revision: Union[str, Sequence[str], None] = "k1l2m3n4o5p6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_teams 中間テーブル作成
    op.create_table(
        "user_teams",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "team_id"),
    )
    # チームからユーザーを逆引きするためのインデックス作成
    op.create_index("ix_user_teams_team_id", "user_teams", ["team_id"], unique=False)

    # 2. 既存データの移行 (users.team_id -> user_teams)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            """
            INSERT INTO user_teams (user_id, team_id)
            SELECT id, team_id FROM users WHERE team_id IS NOT NULL
            ON CONFLICT DO NOTHING
            """
        )
    else:
        op.execute(
            """
            INSERT OR IGNORE INTO user_teams (user_id, team_id)
            SELECT id, team_id FROM users WHERE team_id IS NOT NULL
            """
        )

    # 3. users から旧 team_id カラム・制約を削除
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_team_id")
        batch_op.drop_constraint("fk_users_team_id", type_="foreignkey")
        batch_op.drop_column("team_id")


def downgrade() -> None:
    # 1. users に team_id カラム・制約を復元
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("team_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_users_team_id", "teams", ["team_id"], ["id"], ondelete="SET NULL"
        )
        batch_op.create_index("ix_users_team_id", ["team_id"], unique=False)

    # 2. データの復旧（1ユーザー1チームの制限に丸める）
    op.execute(
        """
        UPDATE users SET team_id = (
            SELECT team_id FROM user_teams WHERE user_teams.user_id = users.id LIMIT 1
        )
        """
    )

    # 3. user_teams テーブルを削除
    op.drop_index("ix_user_teams_team_id", table_name="user_teams")
    op.drop_table("user_teams")
