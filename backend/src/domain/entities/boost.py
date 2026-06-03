from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class Boost:
    """
    A paid visibility boost for a hiver. While active (now < expires_at) the hiver
    is ranked ahead of others in search — globally, or within one `vertical`.
    """

    id: str
    hiver_id: str
    expires_at: datetime
    stripe_payment_id: str
    vertical: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def is_active(self, now: datetime | None = None) -> bool:
        ref = now or _utcnow()
        exp = self.expires_at
        # Tolerate naive datetimes (some drivers/paths return tz-naive values).
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=UTC)
        return exp > ref

    @classmethod
    def purchase(
        cls,
        id: str,
        hiver_id: str,
        stripe_payment_id: str,
        days: int = 7,
        vertical: str | None = None,
    ) -> Boost:
        return cls(
            id=id,
            hiver_id=hiver_id,
            stripe_payment_id=stripe_payment_id,
            vertical=vertical,
            expires_at=_utcnow() + timedelta(days=days),
        )
