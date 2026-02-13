"""create conversation and message tables

Revision ID: 002
Revises: 001
Create Date: 2026-02-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversation",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_conversation_user_id", "conversation", ["user_id"])
    op.create_index(
        "ix_conversation_user_updated",
        "conversation",
        ["user_id", sa.text("updated_at DESC")],
    )

    op.create_table(
        "message",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.String(20),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversation.id"], ondelete="CASCADE"
        ),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_message_role"),
    )
    op.create_index("ix_message_conversation_id", "message", ["conversation_id"])
    op.create_index(
        "ix_message_conversation_created",
        "message",
        ["conversation_id", sa.text("created_at ASC")],
    )


def downgrade() -> None:
    op.drop_index("ix_message_conversation_created", table_name="message")
    op.drop_index("ix_message_conversation_id", table_name="message")
    op.drop_table("message")
    op.drop_index("ix_conversation_user_updated", table_name="conversation")
    op.drop_index("ix_conversation_user_id", table_name="conversation")
    op.drop_table("conversation")
