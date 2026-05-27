"""Create PL/pgSQL triggers and stored functions

Revision ID: 014
Revises: 013
Create Date: 2026-05-27

Triggers:
  1. trg_updated_at        — auto-stamps updated_at on every UPDATE
  2. trg_reveal_reviews    — reveals both reviews when both parties submit
  3. trg_update_hiver_rating — recalculates hiver avg_rating + level on new review

Functions:
  find_hivers_in_radius(lat, lng, radius_km, vertical) — PostGIS radius search
"""
from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Trigger 1: auto updated_at ──────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for table in ("users", "tasks", "offers", "transactions"):
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
        """)

    # ── Trigger 2: blind review reveal ──────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_reveal_reviews()
        RETURNS TRIGGER AS $$
        DECLARE
            review_count INT;
        BEGIN
            SELECT COUNT(*) INTO review_count
            FROM reviews
            WHERE task_id = NEW.task_id;

            -- Both reviews submitted: reveal both
            IF review_count >= 2 THEN
                UPDATE reviews
                SET is_revealed = true
                WHERE task_id = NEW.task_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_reveal_reviews
        AFTER INSERT ON reviews
        FOR EACH ROW EXECUTE FUNCTION fn_reveal_reviews();
    """)

    # ── Trigger 3: update hiver avg_rating and level ────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_update_hiver_rating()
        RETURNS TRIGGER AS $$
        DECLARE
            new_avg  DECIMAL(3,2);
            new_level VARCHAR(20);
        BEGIN
            -- Only act when a review about a hiver is revealed
            IF NEW.is_revealed = true AND OLD.is_revealed = false THEN
                SELECT ROUND(AVG(rating)::numeric, 2)
                INTO new_avg
                FROM reviews
                WHERE reviewee_id = NEW.reviewee_id AND is_revealed = true;

                -- Recalculate level based on xp_points
                SELECT CASE
                    WHEN xp_points >= 1500 THEN 'legend'
                    WHEN xp_points >= 500  THEN 'master'
                    WHEN xp_points >= 100  THEN 'experienced'
                    ELSE 'beginner'
                END INTO new_level
                FROM hivers WHERE user_id = NEW.reviewee_id;

                UPDATE hivers
                SET avg_rating      = new_avg,
                    completed_tasks = completed_tasks + 1,
                    review_count    = review_count + 1,
                    xp_points       = xp_points + 10,
                    level           = new_level
                WHERE user_id = NEW.reviewee_id;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("""
        CREATE TRIGGER trg_update_hiver_rating
        AFTER UPDATE OF is_revealed ON reviews
        FOR EACH ROW EXECUTE FUNCTION fn_update_hiver_rating();
    """)

    # ── Function: find_hivers_in_radius ─────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION find_hivers_in_radius(
            center_lat  DOUBLE PRECISION,
            center_lng  DOUBLE PRECISION,
            radius_km   INT,
            p_vertical  VARCHAR DEFAULT NULL
        )
        RETURNS TABLE (
            user_id        VARCHAR,
            distance_m     DOUBLE PRECISION,
            avg_rating     DECIMAL,
            level          VARCHAR,
            is_available   BOOLEAN
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT
                h.user_id,
                ST_Distance(
                    h.location_point::geography,
                    ST_MakePoint(center_lng, center_lat)::geography
                ) AS distance_m,
                h.avg_rating,
                h.level,
                h.is_available_now
            FROM hivers h
            WHERE
                h.location_point IS NOT NULL
                AND h.is_available_now = true
                AND ST_DWithin(
                    h.location_point::geography,
                    ST_MakePoint(center_lng, center_lat)::geography,
                    radius_km * 1000  -- convert km to meters
                )
                AND (p_vertical IS NULL OR EXISTS (
                    SELECT 1 FROM hiver_skills hs
                    JOIN skills s ON s.id = hs.skill_id
                    WHERE hs.hiver_id = h.user_id AND s.vertical = p_vertical
                ))
            ORDER BY distance_m ASC;
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS find_hivers_in_radius")
    op.execute("DROP TRIGGER IF EXISTS trg_update_hiver_rating ON reviews")
    op.execute("DROP FUNCTION IF EXISTS fn_update_hiver_rating")
    op.execute("DROP TRIGGER IF EXISTS trg_reveal_reviews ON reviews")
    op.execute("DROP FUNCTION IF EXISTS fn_reveal_reviews")
    for table in ("transactions", "offers", "tasks", "users"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")
    op.execute("DROP FUNCTION IF EXISTS fn_set_updated_at")
