"""add user_teams and admin auth

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-08-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision: str = "l2m3n4o5p6q7"
down_revision: Union[str, Sequence[str], None] = "k1l2m3n4o5p6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. user_teams 中間テーブル作成（存在しない場合のみ）
    if "user_teams" not in tables:
        op.create_table(
            "user_teams",
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("team_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("user_id", "team_id"),
        )

    # インデックス作成（存在しない場合のみ）
    if "user_teams" in inspector.get_table_names():
        indexes = [idx["name"] for idx in inspector.get_indexes("user_teams")]
        if "ix_user_teams_team_id" not in indexes:
            try:
                op.create_index(
                    "ix_user_teams_team_id", "user_teams", ["team_id"], unique=False
                )
            except Exception:
                pass

    # 2. 既存データ移行 (users.team_id -> user_teams)
    # users テーブルに team_id カラムが存在する場合のみ移行およびドロップ処理を行う
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    if "team_id" in user_columns:
        if conn.dialect.name == "postgresql":
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

        # 3. users から team_id カラムと外部キー、インデックスを削除
        with op.batch_alter_table("users", schema=None) as batch_op:
            user_indexes = [idx["name"] for idx in inspector.get_indexes("users")]
            if "ix_users_team_id" in user_indexes:
                batch_op.drop_index("ix_users_team_id")

            user_fks = inspector.get_foreign_keys("users")
            for fk in user_fks:
                if "team_id" in fk.get("constrained_columns", []):
                    if fk.get("name"):
                        batch_op.drop_constraint(fk["name"], type_="foreignkey")

            batch_op.drop_column("team_id")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    user_columns = [col["name"] for col in inspector.get_columns("users")]

    # 1. users に team_id カラムと制約を戻す（存在しない場合のみ）
    if "team_id" not in user_columns:
        with op.batch_alter_table("users", schema=None) as batch_op:
            batch_op.add_column(sa.Column("team_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key(
                "fk_users_team_id", "teams", ["team_id"], ["id"], ondelete="SET NULL"
            )
            batch_op.create_index("ix_users_team_id", ["team_id"], unique=False)

        # 2. データを user_teams から復元 (1ユーザー1チームの制限に丸める)
        op.execute(
            """
            UPDATE users SET team_id = (
                SELECT team_id FROM user_teams WHERE user_teams.user_id = users.id LIMIT 1
            )
            """
        )

    # 3. user_teams テーブルを削除（存在する場合のみ）
    tables = inspector.get_table_names()
    if "user_teams" in tables:
        user_teams_indexes = [
            idx["name"] for idx in inspector.get_indexes("user_teams")
        ]
        if "ix_user_teams_team_id" in user_teams_indexes:
            op.drop_index("ix_user_teams_team_id", table_name="user_teams")
        op.drop_table("user_teams")
