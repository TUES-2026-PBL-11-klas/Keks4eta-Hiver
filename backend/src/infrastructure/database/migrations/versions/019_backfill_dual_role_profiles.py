"""Backfill dual-role profiles (unified accounts)

Unified accounts: every account is BOTH a client and a hiver (one `users` row
with a `clients` row AND a `hivers` row). Existing accounts were single-role, so
backfill the missing counterpart profile with neutral defaults:
  - client: rating 5.0 (optimistic default, matches Client entity), 0 tasks
  - hiver: rating 0.0 (no reviews yet, matches Rating.default()), beginner, 5 km

Defaults mirror the SQLAlchemy model + domain value-object defaults so a
backfilled row reads back identically to a freshly registered one.

The migration role is the table owner and bypasses the RLS enabled in 017.

Revision ID: 019
Revises: 018
Create Date: 2026-06-04
"""
from alembic import op

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO clients (user_id, rating_as_client, total_tasks, review_count)
        SELECT u.id, 5.0, 0, 0
        FROM users u
        WHERE NOT EXISTS (SELECT 1 FROM clients c WHERE c.user_id = u.id)
        """
    )
    op.execute(
        """
        INSERT INTO hivers (
            user_id, bio, xp_points, level, avg_rating,
            completed_tasks, review_count, is_available_now, work_radius_km
        )
        SELECT u.id, '', 0, 'beginner', 0.0, 0, 0, false, 5
        FROM users u
        WHERE NOT EXISTS (SELECT 1 FROM hivers h WHERE h.user_id = u.id)
        """
    )


def downgrade() -> None:
    # Not cleanly reversible: backfilled rows are indistinguishable from rows a
    # user created organically. No-op to avoid deleting real profiles.
    pass
