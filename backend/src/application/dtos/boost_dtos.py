from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

# Fixed pricing for the demo (mock-charged via the payment port).
BOOST_PRICE_BGN = 5.0
BOOST_DURATION_DAYS = 7


class BuyBoostRequest(BaseModel):
    # Optional: scope the boost to one vertical; omit for a global boost.
    vertical: str | None = None


class BoostResponse(BaseModel):
    id: str
    hiver_id: str
    vertical: str | None = None
    expires_at: datetime
    created_at: datetime
    is_active: bool
    price_bgn: float = BOOST_PRICE_BGN

    model_config = {"from_attributes": True}
