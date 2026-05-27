"""Create reviews table

Revision ID: 008
Revises: 007
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id",          sa.String(36),    primary_key=True),
        sa.Column("task_id",     sa.String(36),    nullable=False),
        sa.Column("reviewer_id", sa.String(36),    nullable=False),
        sa.Column("reviewee_id", sa.String(36),    nullable=False),
        sa.Column("rating",      sa.DECIMAL(3, 2), nullable=False),
        sa.Column("comment",     sa.Text(),        nullable=False),
        sa.Column("is_revealed", sa.Boolean(),     nullable=False, server_default="false"),
        sa.Column("created_at",  sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"],     ["tasks.id"],   ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewee_id"], ["users.id"]),
        # Each user can only review the other once per task
        sa.UniqueConstraint("task_id", "reviewer_id", name="uq_review_task_reviewer"),
    )
    op.create_index("ix_reviews_task_id",     "reviews", ["task_id"])
    op.create_index("ix_reviews_reviewee_id", "reviews", ["reviewee_id"])


def downgrade() -> None:
    op.drop_index("ix_reviews_reviewee_id", table_name="reviews")
    op.drop_index("ix_reviews_task_id",     table_name="reviews")
    op.drop_table("reviews")
