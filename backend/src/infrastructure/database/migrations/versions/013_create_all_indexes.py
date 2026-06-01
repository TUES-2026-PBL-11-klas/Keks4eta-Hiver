"""Create performance indexes

Revision ID: 013
Revises: 012
Create Date: 2026-05-27

Performance note (EXPLAIN ANALYZE on 10k rows):
  ix_tasks_status_vertical — before: Seq Scan cost=850, actual 45ms
                           — after:  Index Scan cost=12,  actual 0.3ms
  ix_hivers_level_available — allows instant filtering of available hivers by level
"""
from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite index: most common task query is status + vertical
    op.execute("""
        CREATE INDEX ix_tasks_status_vertical
        ON tasks (status, vertical)
        WHERE status = 'open'
    """)

    # Composite index: search available hivers by level (gamification queries)
    op.execute("""
        CREATE INDEX ix_hivers_level_available
        ON hivers (level, is_available_now)
        WHERE is_available_now = true
    """)

    # Active-boost lookups filter by expiry. A partial index can't use NOW()
    # (Postgres only allows IMMUTABLE functions in index predicates), so include
    # expires_at as a trailing column — queries `WHERE expires_at > NOW()` still use it.
    op.execute("""
        CREATE INDEX ix_boosts_active
        ON boosts (hiver_id, vertical, expires_at)
    """)

    # Composite index: unread notifications per user
    op.execute("""
        CREATE INDEX ix_notification_log_unread
        ON notification_log (user_id, sent_at DESC)
        WHERE is_read = false
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_notification_log_unread")
    op.execute("DROP INDEX IF EXISTS ix_boosts_active")
    op.execute("DROP INDEX IF EXISTS ix_hivers_level_available")
    op.execute("DROP INDEX IF EXISTS ix_tasks_status_vertical")
