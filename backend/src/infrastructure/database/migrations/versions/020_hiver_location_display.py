"""Add location_display to hivers

Phase 4 (profiles): a hiver can now set a service location from their profile.
The PostGIS `location_point` already existed (used by nearby-hiver search) but
the human-readable address picked in the UI had nowhere to live, so the Settings
form could never prefill it. Add a nullable display column alongside the point.

Revision ID: 020
Revises: 019
Create Date: 2026-06-04
"""
import sqlalchemy as sa
from alembic import op

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "hivers",
        sa.Column("location_display", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("hivers", "location_display")
