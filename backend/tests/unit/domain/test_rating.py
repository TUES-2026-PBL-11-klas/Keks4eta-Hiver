import pytest

from domain.value_objects.rating import Rating


class TestRatingConstruction:
    @pytest.mark.parametrize("value", [0.0, 2.5, 5.0])
    def test_valid_range(self, value):
        assert Rating(value).value == value

    @pytest.mark.parametrize("value", [-0.1, 5.1, 100.0])
    def test_out_of_range_rejected(self, value):
        with pytest.raises(ValueError, match="between 0.0 and 5.0"):
            Rating(value)

    def test_factories(self):
        assert Rating.default().value == 0.0
        assert Rating.perfect().value == 5.0


class TestRatingBusinessRules:
    def test_is_acceptable_threshold(self):
        assert Rating(2.0).is_acceptable()
        assert not Rating(1.9).is_acceptable()

    def test_recalculate_from_zero_count_uses_new_score(self):
        assert Rating(0.0).recalculate(0, 4.0).value == 4.0

    def test_recalculate_rolling_average(self):
        # one prior score of 4.0, new score 5.0 -> avg 4.5
        assert Rating(4.0).recalculate(1, 5.0).value == 4.5

    def test_recalculate_rounds_to_two_dp(self):
        # avg of 5.0 (x2) and 4.0 -> 4.666... -> 4.67
        assert Rating(5.0).recalculate(2, 4.0).value == 4.67
