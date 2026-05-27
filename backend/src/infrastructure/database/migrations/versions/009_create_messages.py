"""Create messages table

Revision ID: 009
Revises: 008
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id",         sa.String(36), primary_key=True),
        sa.Column("task_id",    sa.String(36), nullable=False),
        sa.Column("sender_id",  sa.String(36), nullable=False),
        sa.Column("content",    sa.Text(),     nullable=False),
        sa.Column("is_read",    sa.Boolean(),  nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"],   ["tasks.id"],  ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"]),
    )
    op.create_index("ix_messages_task_id",    "messages", ["task_id"])
    op.create_index("ix_messages_created_at", "messages", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_messages_created_at", table_name="messages")
    op.drop_index("ix_messages_task_id",    table_name="messages")
    op.drop_table("messages")
