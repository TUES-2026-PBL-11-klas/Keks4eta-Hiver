"""Create users table

Revision ID: 002
Revises: 001
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id",            sa.String(36),  primary_key=True),
        sa.Column("email",         sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name",     sa.String(100), nullable=False),
        sa.Column("phone",         sa.String(20)),
        sa.Column("avatar_url",    sa.String(500)),
        sa.Column("role",          sa.String(10),  nullable=False),  # client | hiver
        sa.Column("is_active",     sa.Boolean(),   nullable=False, server_default="true"),
        sa.Column("created_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role",  "users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_users_role",  table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
