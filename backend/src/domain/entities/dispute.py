from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from src.domain.errors.domain_errors import DisputeAlreadyResolvedError


class DisputeStatus(StrEnum):
    OPEN = "open"          # raised, escrow locked, awaiting resolution
    RESOLVED = "resolved"  # settled in the hiver's favour → escrow released
    REFUNDED = "refunded"  # settled in the client's favour → escrow refunded


@dataclass
class Dispute:
    """
    A dispute on a task's escrow. One per task (DB-unique on task_id).

    Resolution is by *concession*: the client can concede and release the held
    funds to the hiver (RESOLVED), or the hiver can concede and refund the client
    (REFUNDED). Either ends the dispute; neither party can grant themselves money.
    """
    id: str
    task_id: str
    opened_by_id: str
    reason: str
    status: DisputeStatus = DisputeStatus.OPEN
    admin_note: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.reason or not self.reason.strip():
            raise ValueError("Dispute reason cannot be empty")
        self.reason = self.reason.strip()

    def _assert_open(self) -> None:
        if self.status != DisputeStatus.OPEN:
            raise DisputeAlreadyResolvedError(self.task_id)

    def resolve_release(self, note: str | None = None) -> None:
        """Client concedes — funds go to the hiver."""
        self._assert_open()
        self.status = DisputeStatus.RESOLVED
        self.admin_note = note
        self.resolved_at = datetime.utcnow()

    def resolve_refund(self, note: str | None = None) -> None:
        """Hiver concedes — funds are refunded to the client."""
        self._assert_open()
        self.status = DisputeStatus.REFUNDED
        self.admin_note = note
        self.resolved_at = datetime.utcnow()

    def is_open(self) -> bool:
        return self.status == DisputeStatus.OPEN
