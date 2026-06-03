from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Money:
    """
    Value Object: Money with currency.
    Immutable — every operation returns a new Money instance.
    OOP: Encapsulation — arithmetic never leaks raw floats.
    """
    value: Decimal
    currency: str = "BGN"

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"Money value cannot be negative: {self.value}")
        object.__setattr__(self, "value", self.value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @classmethod
    def of(cls, amount: float | int | str | Decimal, currency: str = "BGN") -> Money:
        return cls(value=Decimal(str(amount)), currency=currency)

    def __add__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        return Money(self.value + other.value, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._assert_same_currency(other)
        result = self.value - other.value
        if result < 0:
            raise ValueError("Subtraction would result in negative Money")
        return Money(result, self.currency)

    def __mul__(self, factor: float | Decimal) -> Money:
        result = (self.value * Decimal(str(factor))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Money(result, self.currency)

    def __gt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.value > other.value

    def __ge__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.value >= other.value

    def __lt__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.value < other.value

    def __le__(self, other: Money) -> bool:
        self._assert_same_currency(other)
        return self.value <= other.value

    def is_zero(self) -> bool:
        return self.value == Decimal("0.00")

    def _assert_same_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(f"Currency mismatch: {self.currency} vs {other.currency}")

    def __repr__(self) -> str:
        return f"{self.value} {self.currency}"
