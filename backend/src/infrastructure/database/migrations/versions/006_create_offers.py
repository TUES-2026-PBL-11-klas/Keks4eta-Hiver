"""Create offers table

Revision ID: 006
Revises: 005
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "offers",
        sa.Column("id",              sa.String(36),    primary_key=True),
        sa.Column("task_id",         sa.String(36),    nullable=False),
        sa.Column("hiver_id",        sa.String(36),    nullable=False),
        sa.Column("price",           sa.DECIMAL(10,2), nullable=False),
        sa.Column("message",         sa.Text(),        nullable=False),
        sa.Column("estimated_hours", sa.DECIMAL(5,2),  nullable=False),
        sa.Column("status",          sa.String(20),    nullable=False, server_default="pending"),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",      sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"],  ["tasks.id"],        ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["hiver_id"], ["hivers.user_id"]),
        # One hiver can only bid once per task
        sa.UniqueConstraint("task_id", "hiver_id", name="uq_offer_task_hiver"),
    )
    op.create_index("ix_offers_task_id",  "offers", ["task_id"])
    op.create_index("ix_offers_hiver_id", "offers", ["hiver_id"])
    op.create_index("ix_offers_status",   "offers", ["status"])


def downgrade() -> None:
    op.drop_index("ix_offers_status",   table_name="offers")
    op.drop_index("ix_offers_hiver_id", table_name="offers")
    op.drop_index("ix_offers_task_id",  table_name="offers")
    op.drop_table("offers")
