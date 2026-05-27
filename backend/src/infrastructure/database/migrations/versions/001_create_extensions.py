"""Create PostgreSQL extensions: PostGIS, uuid-ossp, pgcrypto

Revision ID: 001
Revises:
Create Date: 2026-05-27
"""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis"')


def downgrade() -> None:
    # Extensions are shared — only drop in dev, never in prod
    op.execute('DROP EXTENSION IF EXISTS "postgis"')
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
