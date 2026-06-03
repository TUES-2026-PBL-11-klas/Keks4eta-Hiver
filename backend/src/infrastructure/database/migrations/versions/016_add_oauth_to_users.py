"""Add OAuth (Google/Facebook) support to users

Makes password_hash nullable (OAuth-only accounts have no password) and adds
oauth_provider + oauth_id columns with a unique index so a provider account
maps to exactly one user.

Revision ID: 016
Revises: 015
Create Date: 2026-05-31
"""
import sqlalchemy as sa
from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # OAuth-only accounts never have a password.
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)

    op.add_column("users", sa.Column("oauth_provider", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("oauth_id", sa.String(255), nullable=True))

    # One provider identity -> one user. Partial unique so NULLs (password users) don't collide.
    op.create_index(
        "uq_users_oauth_identity",
        "users",
        ["oauth_provider", "oauth_id"],
        unique=True,
        postgresql_where=sa.text("oauth_provider IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_users_oauth_identity", table_name="users")
    op.drop_column("users", "oauth_id")
    op.drop_column("users", "oauth_provider")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
