from __future__ import annotations

from dataclasses import dataclass

ALLOWED_RADII_KM = (1, 2, 5, 10, 15, 20)


@dataclass(frozen=True)
class WorkRadius:
    """
    Value Object: Hiver's maximum work radius in km.
    Constrained to predefined tiers — not arbitrary float.
    OOP: Encapsulation — enforcement of allowed values inside object.
    """
    km: int

    def __post_init__(self) -> None:
        if self.km not in ALLOWED_RADII_KM:
            raise ValueError(
                f"WorkRadius must be one of {ALLOWED_RADII_KM}, got {self.km}"
            )

    @classmethod
    def default(cls) -> WorkRadius:
        return cls(5)

    @classmethod
    def maximum(cls) -> WorkRadius:
        return cls(20)

    def covers(self, distance_km: float) -> bool:
        return distance_km <= self.km

    def __repr__(self) -> str:
        return f"WorkRadius({self.km}km)"
