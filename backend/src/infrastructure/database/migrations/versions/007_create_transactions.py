"""Create transactions table (escrow)

Revision ID: 007
Revises: 006
Create Date: 2026-05-27
"""
import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id",                       sa.String(36),    primary_key=True),
        sa.Column("task_id",                  sa.String(36),    nullable=False, unique=True),
        sa.Column("client_id",                sa.String(36),    nullable=False),
        sa.Column("hiver_id",                 sa.String(36),    nullable=False),
        sa.Column("gross_amount",             sa.DECIMAL(10,2), nullable=False),
        sa.Column("platform_fee",             sa.DECIMAL(10,2), nullable=False),
        sa.Column("hiver_payout",             sa.DECIMAL(10,2), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(200),   nullable=False),
        sa.Column("status",                   sa.String(20),    nullable=False, server_default="held"),
        sa.Column("released_at",  sa.DateTime(timezone=True)),
        sa.Column("refunded_at",  sa.DateTime(timezone=True)),
        sa.Column("created_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at",   sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["task_id"],   ["tasks.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.user_id"]),
        sa.ForeignKeyConstraint(["hiver_id"],  ["hivers.user_id"]),
    )
    op.create_index("ix_transactions_status",    "transactions", ["status"])
    op.create_index("ix_transactions_hiver_id",  "transactions", ["hiver_id"])
    op.create_index("ix_transactions_client_id", "transactions", ["client_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_client_id", table_name="transactions")
    op.drop_index("ix_transactions_hiver_id",  table_name="transactions")
    op.drop_index("ix_transactions_status",    table_name="transactions")
    op.drop_table("transactions")
