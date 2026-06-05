"""Create favorites table

Phase 5: users can save tasks and hivers. One polymorphic table keyed by
(user_id, target_type, target_id), unique so a save is idempotent. RLS is
enabled (default-deny, no policies) to match migration 017 — the backend
connects as the table owner (BYPASSRLS), so Supabase's auto PostgREST API can't
read it but the app keeps working.

Revision ID: 021
Revises: 020
Create Date: 2026-06-04
"""
import sqlalchemy as sa
from alembic import op

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favorites",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(length=36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_type", sa.String(length=10), nullable=False),
        sa.Column("target_id", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "target_type", "target_id", name="uq_favorite"
        ),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    # Match the security posture of migration 017: lock the auto-exposed API.
    op.execute("ALTER TABLE public.favorites ENABLE ROW LEVEL SECURITY;")


def downgrade() -> None:
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")
