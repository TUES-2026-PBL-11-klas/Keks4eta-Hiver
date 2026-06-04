from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt


@dataclass(frozen=True)
class Location:
    """
    Value Object: Geographic point (WGS 84).
    Immutable — coordinates never mutate after construction.
    OOP: Encapsulation — distance logic stays inside Location.
    """
    latitude: float
    longitude: float
    display_address: str | None = None

    def __post_init__(self) -> None:
        if not (-90.0 <= self.latitude <= 90.0):
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not (-180.0 <= self.longitude <= 180.0):
            raise ValueError(f"Invalid longitude: {self.longitude}")

    def distance_to_meters(self, other: Location) -> float:
        """Haversine formula — great-circle distance in meters."""
        R = 6_371_000
        phi1, phi2 = radians(self.latitude), radians(other.latitude)
        dphi = radians(other.latitude - self.latitude)
        dlambda = radians(other.longitude - self.longitude)
        a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    def distance_to_km(self, other: Location) -> float:
        return round(self.distance_to_meters(other) / 1000, 2)

    def is_within_km(self, other: Location, radius_km: float) -> bool:
        return self.distance_to_km(other) <= radius_km

    def __repr__(self) -> str:
        return f"Location({self.latitude}, {self.longitude})"
