"""Create boosts table

Revision ID: 011
Revises: 010
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "boosts",
        sa.Column("id",                sa.String(36), primary_key=True),
        sa.Column("hiver_id",          sa.String(36), nullable=False),
        sa.Column("vertical",          sa.String(20)),
        sa.Column("expires_at",        sa.DateTime(timezone=True), nullable=False),
        sa.Column("stripe_payment_id", sa.String(200), nullable=False),
        sa.Column("created_at",        sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["hiver_id"], ["hivers.user_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_boosts_hiver_id",   "boosts", ["hiver_id"])
    op.create_index("ix_boosts_expires_at", "boosts", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_boosts_expires_at", table_name="boosts")
    op.drop_index("ix_boosts_hiver_id",   table_name="boosts")
    op.drop_table("boosts")
