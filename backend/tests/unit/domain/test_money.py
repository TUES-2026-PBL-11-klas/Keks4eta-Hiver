from decimal import Decimal

import pytest

from domain.value_objects.money import Money


class TestMoneyConstruction:
    def test_quantizes_to_two_decimals(self):
        assert Money(Decimal("10.005")).value == Decimal("10.01")  # ROUND_HALF_UP

    def test_negative_value_rejected(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(Decimal("-1"))

    def test_default_currency_is_bgn(self):
        assert Money(Decimal("5")).currency == "BGN"

    def test_of_accepts_int_float_str(self):
        assert Money.of(10).value == Decimal("10.00")
        assert Money.of("12.5").value == Decimal("12.50")
        assert Money.of(3.5, "EUR").currency == "EUR"

    def test_is_frozen(self):
        m = Money.of(1)
        with pytest.raises(Exception):
            m.value = Decimal("2")  # type: ignore[misc]


class TestMoneyArithmetic:
    def test_add(self):
        assert (Money.of(10) + Money.of(5)).value == Decimal("15.00")

    def test_sub(self):
        assert (Money.of(10) - Money.of(4)).value == Decimal("6.00")

    def test_sub_into_negative_rejected(self):
        with pytest.raises(ValueError, match="negative Money"):
            Money.of(5) - Money.of(10)

    def test_mul_rounds_half_up(self):
        assert (Money.of(10) * 0.105).value == Decimal("1.05")

    def test_currency_mismatch_on_add(self):
        with pytest.raises(ValueError, match="Currency mismatch"):
            Money.of(1, "BGN") + Money.of(1, "EUR")


class TestMoneyComparison:
    def test_ordering(self):
        assert Money.of(10) > Money.of(5)
        assert Money.of(5) < Money.of(10)
        assert Money.of(5) >= Money.of(5)
        assert Money.of(5) <= Money.of(5)

    def test_is_zero(self):
        assert Money.of(0).is_zero()
        assert not Money.of(1).is_zero()

    def test_comparison_currency_mismatch(self):
        with pytest.raises(ValueError, match="Currency mismatch"):
            _ = Money.of(1, "BGN") > Money.of(1, "EUR")
