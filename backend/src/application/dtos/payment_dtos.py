from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class EscrowResponse(BaseModel):
    """Escrow / transaction summary for a task (owner + assigned hiver view)."""
    task_id: str
    status: str  # held | released | refunded | disputed
    gross_amount: float
    platform_fee: float
    hiver_payout: float
    created_at: datetime
    released_at: datetime | None = None
    refunded_at: datetime | None = None

    model_config = {"from_attributes": True}
