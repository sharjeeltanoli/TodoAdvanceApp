"""Add event-driven tables: task_event, notification, processed_event

Revision ID: 005
Revises: 004
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # task_event table (audit trail)
    op.create_table(
        "task_event",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("task_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("data", JSONB, nullable=False),
        sa.Column("changed_fields", JSONB, nullable=True),
        sa.Column("event_source", sa.String(50), server_default="api"),
        sa.CheckConstraint(
            "event_type IN ('created', 'updated', 'deleted', 'completed')",
            name="valid_event_type",
        ),
    )
    op.create_index("idx_task_event_task_id", "task_event", ["task_id"])
    op.create_index("idx_task_event_user_id", "task_event", ["user_id"])
    op.create_index("idx_task_event_timestamp", "task_event", ["timestamp"], postgresql_using="btree")

    # notification table
    op.create_table(
        "notification",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("read", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "type IN ('reminder_upcoming', 'reminder_overdue', 'task_recurring')",
            name="valid_notification_type",
        ),
    )
    op.create_index("idx_notification_user_id", "notification", ["user_id"])
    op.create_index(
        "idx_notification_user_unread",
        "notification",
        ["user_id", "read"],
        postgresql_where=sa.text("read = false"),
    )

    # processed_event table (idempotency)
    op.create_table(
        "processed_event",
        sa.Column("event_id", sa.String(255), primary_key=True),
        sa.Column("consumer_group", sa.String(100), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_processed_event_age", "processed_event", ["processed_at"])


def downgrade() -> None:
    op.drop_table("processed_event")
    op.drop_table("notification")
    op.drop_table("task_event")
