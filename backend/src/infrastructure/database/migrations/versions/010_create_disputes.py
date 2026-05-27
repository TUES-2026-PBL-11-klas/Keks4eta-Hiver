"""Create disputes table

Revision ID: 010
Revises: 009
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "disputes",
        sa.Column("id",           sa.String(36), primary_key=True),
        sa.Column("task_id",      sa.String(36), nullable=False, unique=True),
        sa.Column("opened_by_id", sa.String(36), nullable=False),
        sa.Column("reason",       sa.Text(),     nullable=False),
        sa.Column("status",       sa.String(20), nullable=False, server_default="open"),
        sa.Column("admin_note",   sa.Text()),
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at",  sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["task_id"],      ["tasks.id"],  ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opened_by_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_table("disputes")
