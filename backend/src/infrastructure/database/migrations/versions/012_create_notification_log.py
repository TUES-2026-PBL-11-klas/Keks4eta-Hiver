"""Create notification_log table

Revision ID: 012
Revises: 011
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_log",
        sa.Column("id",      sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("title",   sa.String(200), nullable=False),
        sa.Column("body",    sa.Text(),     nullable=False),
        sa.Column("data",    postgresql.JSONB(), server_default="{}"),
        sa.Column("is_read", sa.Boolean(),  nullable=False, server_default="false"),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notification_log_user_id", "notification_log", ["user_id"])
    op.create_index("ix_notification_log_sent_at", "notification_log", ["sent_at"])


def downgrade() -> None:
    op.drop_index("ix_notification_log_sent_at", table_name="notification_log")
    op.drop_index("ix_notification_log_user_id", table_name="notification_log")
    op.drop_table("notification_log")
