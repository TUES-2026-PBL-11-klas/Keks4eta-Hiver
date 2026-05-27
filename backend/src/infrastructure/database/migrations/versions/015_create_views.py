"""Create database views

Revision ID: 015
Revises: 014
Create Date: 2026-05-27

Views:
  hiver_earnings_monthly — monthly earnings per hiver with window functions:
    RANK() by earnings within each month, running total, 3-month rolling avg
"""
from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE OR REPLACE VIEW hiver_earnings_monthly AS
        SELECT
            t.hiver_id,
            DATE_TRUNC('month', t.released_at)          AS month,
            COUNT(*)                                     AS tasks_completed,
            SUM(t.hiver_payout)                          AS monthly_earnings,

            -- RANK: position within month by earnings (window function)
            RANK() OVER (
                PARTITION BY DATE_TRUNC('month', t.released_at)
                ORDER BY SUM(t.hiver_payout) DESC
            )                                            AS rank_in_month,

            -- Running total since account creation
            SUM(SUM(t.hiver_payout)) OVER (
                PARTITION BY t.hiver_id
                ORDER BY DATE_TRUNC('month', t.released_at)
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )                                            AS running_total,

            -- 3-month rolling average
            AVG(SUM(t.hiver_payout)) OVER (
                PARTITION BY t.hiver_id
                ORDER BY DATE_TRUNC('month', t.released_at)
                ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
            )                                            AS rolling_3mo_avg

        FROM transactions t
        WHERE t.status = 'released'
          AND t.released_at IS NOT NULL
        GROUP BY t.hiver_id, DATE_TRUNC('month', t.released_at);
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS hiver_earnings_monthly")
