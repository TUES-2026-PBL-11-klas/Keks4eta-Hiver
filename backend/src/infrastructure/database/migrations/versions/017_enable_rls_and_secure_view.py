"""Enable Row Level Security and harden the earnings view

Revision ID: 017
Revises: 016
Create Date: 2026-06-02

Why:
  The database is hosted on Supabase, which automatically exposes the whole
  `public` schema through its PostgREST data API (reachable with the public
  `anon` key). This app never uses that API — the frontend talks to the FastAPI
  backend over a direct Postgres connection — so the auto-API is an unused, open
  door. Supabase's security linter flags it as 15 ERROR-level findings:
    * rls_disabled_in_public — RLS off on all 14 public tables
    * security_definer_view  — `hiver_earnings_monthly` ignores the caller's RLS

Fix:
  1. Enable RLS on every public table. With NO policies attached this is
     "default-deny" for the anon/authenticated API roles, slamming the public
     API shut. The backend connects as the table owner (BYPASSRLS), so it is
     completely unaffected — the app keeps working exactly as before.
  2. Recreate the view WITH (security_invoker = on) so it runs with the querying
     user's privileges instead of the creator's, and therefore respects the RLS
     above instead of leaking earnings past it. (Requires Postgres 15+; Supabase
     runs 15+.)
"""
from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None

# Every table in the public schema that PostgREST exposes. `alembic_version` is
# Alembic's own bookkeeping table — it has no business being readable either.
RLS_TABLES = (
    "users",
    "clients",
    "hivers",
    "hiver_skills",
    "skills",
    "tasks",
    "offers",
    "transactions",
    "reviews",
    "messages",
    "disputes",
    "boosts",
    "notification_log",
    "alembic_version",
)


def upgrade() -> None:
    # ── 1. Lock the public API: enable RLS (default-deny, no policies) ───
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;")

    # ── 2. Make the earnings view respect the caller's RLS ──────────────
    op.execute("""
        CREATE OR REPLACE VIEW public.hiver_earnings_monthly
        WITH (security_invoker = on) AS
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
    # Restore the view to its definer-rights form (migration 015's definition).
    op.execute("""
        CREATE OR REPLACE VIEW public.hiver_earnings_monthly AS
        SELECT
            t.hiver_id,
            DATE_TRUNC('month', t.released_at)          AS month,
            COUNT(*)                                     AS tasks_completed,
            SUM(t.hiver_payout)                          AS monthly_earnings,
            RANK() OVER (
                PARTITION BY DATE_TRUNC('month', t.released_at)
                ORDER BY SUM(t.hiver_payout) DESC
            )                                            AS rank_in_month,
            SUM(SUM(t.hiver_payout)) OVER (
                PARTITION BY t.hiver_id
                ORDER BY DATE_TRUNC('month', t.released_at)
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            )                                            AS running_total,
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

    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE public.{table} DISABLE ROW LEVEL SECURITY;")
