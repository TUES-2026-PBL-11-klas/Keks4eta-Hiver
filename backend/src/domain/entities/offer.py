from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from domain.value_objects.money import Money
from domain.errors.domain_errors import UnauthorizedActionError


class OfferStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


@dataclass
class Offer:
    """
    Domain entity: a bid submitted by a Hiver for an open Task.

    OOP: Encapsulation — status changes are gated through methods
    that enforce business rules.
    """
    id: str
    task_id: str
    hiver_id: str
    price: Money
    message: str
    estimated_hours: float
    status: OfferStatus = OfferStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def accept(self, client_id_acting: str, task_client_id: str) -> None:
        """Client accepts this offer."""
        if client_id_acting != task_client_id:
            raise UnauthorizedActionError("accept offers for this task")
        self.status = OfferStatus.ACCEPTED
        self._touch()

    def reject(self, client_id_acting: str, task_client_id: str) -> None:
        """Client rejects this offer."""
        if client_id_acting != task_client_id:
            raise UnauthorizedActionError("reject offers for this task")
        self.status = OfferStatus.REJECTED
        self._touch()

    def withdraw(self, actor_id: str) -> None:
        """Hiver withdraws their own offer."""
        if actor_id != self.hiver_id:
            raise UnauthorizedActionError("withdraw this offer")
        self.status = OfferStatus.WITHDRAWN
        self._touch()

    def is_pending(self) -> bool:
        return self.status == OfferStatus.PENDING

    def platform_fee(self) -> Money:
        """Platform keeps 10% of the offer price."""
        return self.price * 0.10

    def hiver_payout(self) -> Money:
        """Amount hiver receives after platform fee."""
        return self.price - self.platform_fee()

    def _touch(self) -> None:
        self.updated_at = datetime.utcnow()
