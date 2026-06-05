"""Add featured_until to tasks (paid promotion)

Phase 5: a task owner can pay to promote their task. While now < featured_until
the task is pinned atop search results. Indexed because search orders by it.

Revision ID: 022
Revises: 021
Create Date: 2026-06-04
"""
import sqlalchemy as sa
from alembic import op

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("featured_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_tasks_featured_until", "tasks", ["featured_until"])


def downgrade() -> None:
    op.drop_index("ix_tasks_featured_until", table_name="tasks")
    op.drop_column("tasks", "featured_until")
