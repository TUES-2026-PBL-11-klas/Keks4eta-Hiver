from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from domain.value_objects.money import Money
from domain.errors.domain_errors import EscrowAlreadyReleasedError, TaskNotCompletedError


class TransactionStatus(str, Enum):
    HELD = "held"          # escrow: funds captured, not yet released
    RELEASED = "released"  # hiver received payout
    REFUNDED = "refunded"  # client refunded (cancellation)
    DISPUTED = "disputed"  # under review


@dataclass
class Transaction:
    """
    Domain entity: Stripe escrow transaction linked to a Task.

    OOP: Encapsulation — financial state transitions gated via methods.
    The entity knows its own valid transitions; no external code
    can set status = "released" directly.
    """
    id: str
    task_id: str
    client_id: str
    hiver_id: str
    gross_amount: Money       # full amount charged to client
    platform_fee: Money       # platform keeps this
    hiver_payout: Money       # hiver receives this on release
    stripe_payment_intent_id: str
    status: TransactionStatus = TransactionStatus.HELD
    released_at: datetime | None = None
    refunded_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def release(self) -> None:
        """Release escrow to hiver after task completion."""
        if self.status == TransactionStatus.RELEASED:
            raise EscrowAlreadyReleasedError(self.task_id)
        if self.status != TransactionStatus.HELD:
            raise TaskNotCompletedError(self.task_id)
        self.status = TransactionStatus.RELEASED
        self.released_at = datetime.utcnow()
        self._touch()

    def refund(self) -> None:
        """Refund to client on cancellation."""
        if self.status == TransactionStatus.RELEASED:
            raise EscrowAlreadyReleasedError(self.task_id)
        self.status = TransactionStatus.REFUNDED
        self.refunded_at = datetime.utcnow()
        self._touch()

    def dispute(self) -> None:
        self.status = TransactionStatus.DISPUTED
        self._touch()

    def is_held(self) -> bool:
        return self.status == TransactionStatus.HELD

    def is_released(self) -> bool:
        return self.status == TransactionStatus.RELEASED

    @classmethod
    def create_for_task(
        cls,
        id: str,
        task_id: str,
        client_id: str,
        hiver_id: str,
        offer_price: Money,
        stripe_payment_intent_id: str,
    ) -> "Transaction":
        """Factory method: compute fees and build Transaction in one call."""
        platform_fee = offer_price * 0.10
        hiver_payout = offer_price - platform_fee
        return cls(
            id=id,
            task_id=task_id,
            client_id=client_id,
            hiver_id=hiver_id,
            gross_amount=offer_price,
            platform_fee=platform_fee,
            hiver_payout=hiver_payout,
            stripe_payment_intent_id=stripe_payment_intent_id,
        )

    def _touch(self) -> None:
        self.updated_at = datetime.utcnow()
