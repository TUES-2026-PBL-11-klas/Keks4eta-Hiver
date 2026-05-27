"""Create clients and hivers tables

Revision ID: 003
Revises: 002
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("user_id",           sa.String(36),    primary_key=True),
        sa.Column("rating_as_client",  sa.DECIMAL(3, 2), nullable=False, server_default="5.00"),
        sa.Column("total_tasks",       sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("review_count",      sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("stripe_customer_id",sa.String(100)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Geography column requires PostGIS — added via raw SQL
    op.create_table(
        "hivers",
        sa.Column("user_id",           sa.String(36),    primary_key=True),
        sa.Column("bio",               sa.Text(),        nullable=False, server_default=""),
        sa.Column("xp_points",         sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("level",             sa.String(20),    nullable=False, server_default="beginner"),
        sa.Column("avg_rating",        sa.DECIMAL(3, 2), nullable=False, server_default="0.00"),
        sa.Column("completed_tasks",   sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("review_count",      sa.Integer(),     nullable=False, server_default="0"),
        sa.Column("is_available_now",  sa.Boolean(),     nullable=False, server_default="false"),
        sa.Column("work_radius_km",    sa.Integer(),     nullable=False, server_default="5"),
        sa.Column("stripe_account_id", sa.String(100)),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    # Add PostGIS Geography column separately (not supported by create_table DDL)
    op.execute("ALTER TABLE hivers ADD COLUMN location_point GEOGRAPHY(POINT, 4326)")
    op.execute("CREATE INDEX ix_hivers_location ON hivers USING GIST(location_point)")


def downgrade() -> None:
    op.drop_table("hivers")
    op.drop_table("clients")
