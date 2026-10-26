"""add reminders and summary cache tables

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-10-20

"""

from alembic import op
import sqlalchemy as sa

revision = "q7r8s9t0u1v2"
down_revision = "p6q7r8s9t0u1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. personal_summary_cache テーブル作成
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS personal_summary_cache (
            person_id VARCHAR(64) NOT NULL PRIMARY KEY,
            events TEXT NOT NULL DEFAULT '[]',
            today TEXT NOT NULL DEFAULT '[]',
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
    """
    )

    # 2. task_reminder_logs テーブル作成
    op.create_table(
        "task_reminder_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("note_id", sa.Integer(), nullable=False),
        sa.Column("placement_id", sa.Integer(), nullable=False),
        sa.Column("remind_date", sa.String(length=10), nullable=False),
        sa.Column("slot", sa.String(length=5), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("acked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["placement_id"], ["board_placements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["note_id"], ["sticky_notes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "note_id",
            "remind_date",
            "slot",
            name="uq_task_remind_user_note_date_slot",
        ),
    )

    # 3. calendar_reminder_logs テーブル作成
    op.create_table(
        "calendar_reminder_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=256), nullable=False),
        sa.Column("remind_date", sa.String(length=10), nullable=False),
        sa.Column(
            "remind_kind",
            sa.String(length=16),
            nullable=False,
            server_default="before_15",
        ),
        sa.Column("event_summary", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "event_id",
            "remind_date",
            "remind_kind",
            name="uq_cal_remind_user_event_date_kind",
        ),
    )


def downgrade() -> None:
    op.drop_table("calendar_reminder_logs")
    op.drop_table("task_reminder_logs")
    op.drop_table("personal_summary_cache")
