"""Create skills and hiver_skills tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id",       sa.String(36), primary_key=True),
        sa.Column("name",     sa.String(80), nullable=False),
        sa.Column("vertical", sa.String(20)),
    )
    op.create_index("ix_skills_name", "skills", ["name"], unique=True)

    op.create_table(
        "hiver_skills",
        sa.Column("hiver_id", sa.String(36), nullable=False),
        sa.Column("skill_id", sa.String(36), nullable=False),
        sa.ForeignKeyConstraint(["hiver_id"], ["hivers.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"],      ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("hiver_id", "skill_id"),
    )


def downgrade() -> None:
    op.drop_table("hiver_skills")
    op.drop_index("ix_skills_name", table_name="skills")
    op.drop_table("skills")
