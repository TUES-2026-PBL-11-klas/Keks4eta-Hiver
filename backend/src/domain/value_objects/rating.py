from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Rating:
    """
    Value Object: Rating between 0.0 and 5.0.
    Immutable — always valid, never raw float in domain.
    OOP: Encapsulation — validation inside the object.
    """
    value: float

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 5.0):
            raise ValueError(f"Rating must be between 0.0 and 5.0, got {self.value}")

    @classmethod
    def default(cls) -> "Rating":
        return cls(0.0)

    @classmethod
    def perfect(cls) -> "Rating":
        return cls(5.0)

    def is_acceptable(self) -> bool:
        """Business rule: rating below 2.0 is considered unacceptable."""
        return self.value >= 2.0

    def recalculate(self, current_count: int, new_score: float) -> "Rating":
        """Returns a new Rating that includes the new score in the rolling average."""
        if current_count == 0:
            return Rating(new_score)
        new_avg = (self.value * current_count + new_score) / (current_count + 1)
        return Rating(round(new_avg, 2))

    def __repr__(self) -> str:
        return f"Rating({self.value})"
