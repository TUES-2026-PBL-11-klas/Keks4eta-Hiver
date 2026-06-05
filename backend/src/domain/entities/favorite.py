from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.domain.errors.domain_errors import BusinessRuleViolationError

VALID_TARGETS = {"task", "hiver"}


def _utcnow() -> datetime:
    return datetime.now(UTC)


@dataclass
class Favorite:
    """A user's saved item — a task they want to keep an eye on, or a hiver they
    like. Polymorphic by `target_type` so one table serves both."""

    id: str
    user_id: str
    target_type: str  # "task" | "hiver"
    target_id: str
    created_at: datetime = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        if self.target_type not in VALID_TARGETS:
            raise BusinessRuleViolationError(
                f"target_type must be one of {VALID_TARGETS}", "INVALID_FAVORITE_TARGET"
            )
