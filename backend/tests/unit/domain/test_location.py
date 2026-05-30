import pytest

from domain.value_objects.location import Location


class TestLocationConstruction:
    def test_valid(self):
        loc = Location(42.6977, 23.3219, "Sofia")
        assert loc.latitude == 42.6977
        assert loc.display_address == "Sofia"

    @pytest.mark.parametrize("lat", [-91, 91])
    def test_invalid_latitude(self, lat):
        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(lat, 0)

    @pytest.mark.parametrize("lng", [-181, 181])
    def test_invalid_longitude(self, lng):
        with pytest.raises(ValueError, match="Invalid longitude"):
            Location(0, lng)


class TestLocationDistance:
    def test_zero_distance_to_self(self):
        loc = Location(42.0, 23.0)
        assert loc.distance_to_meters(loc) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance_sofia_to_plovdiv(self):
        sofia = Location(42.6977, 23.3219)
        plovdiv = Location(42.1354, 24.7453)
        # Real-world great-circle distance is ~133 km.
        assert sofia.distance_to_km(plovdiv) == pytest.approx(133, abs=3)

    def test_is_within_km(self):
        sofia = Location(42.6977, 23.3219)
        plovdiv = Location(42.1354, 24.7453)
        assert sofia.is_within_km(plovdiv, 150)
        assert not sofia.is_within_km(plovdiv, 100)
