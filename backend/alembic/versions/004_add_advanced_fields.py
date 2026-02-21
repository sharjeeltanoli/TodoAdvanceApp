"""add advanced task fields

Revision ID: 004
Revises: 002
Create Date: 2026-02-16
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # priority: TEXT NOT NULL DEFAULT 'medium' with CHECK constraint
    op.add_column(
        "task",
        sa.Column(
            "priority",
            sa.Text(),
            nullable=False,
            server_default="medium",
        ),
    )
    op.create_check_constraint(
        "ck_task_priority",
        "task",
        "priority IN ('high', 'medium', 'low')",
    )

    # tags: JSONB NOT NULL DEFAULT '[]'
    op.add_column(
        "task",
        sa.Column(
            "tags",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )

    # due_date: TIMESTAMPTZ NULL
    op.add_column(
        "task",
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
    )

    # recurrence_pattern: JSONB NULL
    op.add_column(
        "task",
        sa.Column("recurrence_pattern", sa.JSON(), nullable=True),
    )

    # reminder_minutes: INTEGER NULL
    op.add_column(
        "task",
        sa.Column("reminder_minutes", sa.Integer(), nullable=True),
    )

    # snoozed_until: TIMESTAMPTZ NULL
    op.add_column(
        "task",
        sa.Column("snoozed_until", sa.DateTime(timezone=True), nullable=True),
    )

    # reminder_notified_at: TIMESTAMPTZ NULL
    op.add_column(
        "task",
        sa.Column(
            "reminder_notified_at", sa.DateTime(timezone=True), nullable=True
        ),
    )

    # parent_task_id: UUID NULL FK -> task.id ON DELETE SET NULL
    op.add_column(
        "task",
        sa.Column("parent_task_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_task_parent",
        "task",
        "task",
        ["parent_task_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Indexes
    op.create_index(
        "ix_task_user_priority", "task", ["user_id", "priority"]
    )
    op.create_index(
        "ix_task_user_due",
        "task",
        ["user_id", "due_date"],
        postgresql_where=sa.text("due_date IS NOT NULL"),
    )
    # JSON type has no default GIN operator class; cast to jsonb for indexing
    op.execute(
        "CREATE INDEX ix_task_tags_gin ON task USING GIN ((tags::jsonb))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_task_tags_gin")
    op.drop_index("ix_task_user_due", table_name="task")
    op.drop_index("ix_task_user_priority", table_name="task")
    op.drop_constraint("fk_task_parent", "task", type_="foreignkey")
    op.drop_column("task", "parent_task_id")
    op.drop_column("task", "reminder_notified_at")
    op.drop_column("task", "snoozed_until")
    op.drop_column("task", "reminder_minutes")
    op.drop_column("task", "recurrence_pattern")
    op.drop_column("task", "due_date")
    op.drop_column("task", "tags")
    op.drop_constraint("ck_task_priority", "task", type_="check")
    op.drop_column("task", "priority")
