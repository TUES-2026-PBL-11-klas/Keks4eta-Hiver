"""Create tasks table

Revision ID: 005
Revises: 004
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id",               sa.String(36),           primary_key=True),
        sa.Column("client_id",        sa.String(36),           nullable=False),
        sa.Column("hiver_id",         sa.String(36)),
        sa.Column("vertical",         sa.String(20),           nullable=False),
        sa.Column("subcategory",      sa.String(50),           nullable=False),
        sa.Column("title",            sa.String(200),          nullable=False),
        sa.Column("description",      sa.Text(),               nullable=False),
        sa.Column("status",           sa.String(20),           nullable=False, server_default="open"),
        sa.Column("budget_min",       sa.DECIMAL(10, 2)),
        sa.Column("budget_max",       sa.DECIMAL(10, 2)),
        sa.Column("is_urgent",        sa.Boolean(),            nullable=False, server_default="false"),
        sa.Column("location_display", sa.String(200)),
        sa.Column("smart_answers",    postgresql.JSONB(),       server_default="{}"),
        sa.Column("image_urls",       postgresql.ARRAY(sa.Text()), server_default="{}"),
        sa.Column("expires_at",       sa.DateTime(timezone=True)),
        sa.Column("created_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",       sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["clients.user_id"]),
        sa.ForeignKeyConstraint(["hiver_id"],  ["hivers.user_id"]),
    )
    op.execute("ALTER TABLE tasks ADD COLUMN location_point GEOGRAPHY(POINT, 4326)")

    op.create_index("ix_tasks_client_id", "tasks", ["client_id"])
    op.create_index("ix_tasks_hiver_id",  "tasks", ["hiver_id"])
    op.create_index("ix_tasks_status",    "tasks", ["status"])
    op.create_index("ix_tasks_vertical",  "tasks", ["vertical"])
    op.create_index("ix_tasks_location",  "tasks", ["location_point"], postgresql_using="gist")


def downgrade() -> None:
    op.drop_index("ix_tasks_location", table_name="tasks")
    op.drop_index("ix_tasks_vertical",  table_name="tasks")
    op.drop_index("ix_tasks_status",    table_name="tasks")
    op.drop_index("ix_tasks_hiver_id",  table_name="tasks")
    op.drop_index("ix_tasks_client_id", table_name="tasks")
    op.drop_table("tasks")
