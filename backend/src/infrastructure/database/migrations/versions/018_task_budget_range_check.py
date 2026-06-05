"""Add budget-range CHECK constraint to tasks

Defence in depth for the min<=max budget rule (also enforced in the domain
entity and the Pydantic DTO). NULLs are allowed on either side (budget is
optional), so the constraint only fires when both bounds are present.

Tasks created before that validation existed can have budget_min > budget_max
(swapped bounds), so normalise any such rows first — otherwise the new
constraint can't be applied. The fix preserves both figures by reordering them.

Revision ID: 018
Revises: 017
Create Date: 2026-06-04
"""
from alembic import op

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Repair legacy rows where the bounds were entered the wrong way round.
    # Postgres evaluates every SET right-hand side against the *original* row,
    # so this is a clean swap, not a min=min collapse. Idempotent: once
    # min <= max, LEAST/GREATEST leave the row untouched.
    op.execute(
        """
        UPDATE tasks
        SET budget_min = LEAST(budget_min, budget_max),
            budget_max = GREATEST(budget_min, budget_max)
        WHERE budget_min IS NOT NULL
          AND budget_max IS NOT NULL
          AND budget_min > budget_max
        """
    )
    op.create_check_constraint(
        "ck_tasks_budget_range",
        "tasks",
        "budget_max IS NULL OR budget_min IS NULL OR budget_min <= budget_max",
    )


def downgrade() -> None:
    op.drop_constraint("ck_tasks_budget_range", "tasks", type_="check")
