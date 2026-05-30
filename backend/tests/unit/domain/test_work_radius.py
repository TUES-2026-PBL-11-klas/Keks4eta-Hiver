import pytest

from domain.value_objects.work_radius import ALLOWED_RADII_KM, WorkRadius


class TestWorkRadius:
    @pytest.mark.parametrize("km", ALLOWED_RADII_KM)
    def test_allowed_tiers(self, km):
        assert WorkRadius(km).km == km

    @pytest.mark.parametrize("km", [0, 3, 7, 25])
    def test_disallowed_values_rejected(self, km):
        with pytest.raises(ValueError, match="must be one of"):
            WorkRadius(km)

    def test_factories(self):
        assert WorkRadius.default().km == 5
        assert WorkRadius.maximum().km == 20

    def test_covers(self):
        r = WorkRadius(5)
        assert r.covers(5.0)
        assert r.covers(4.9)
        assert not r.covers(5.1)
