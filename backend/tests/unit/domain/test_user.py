import pytest

from domain.entities.user import Client, Hiver, User
from domain.errors.domain_errors import InsufficientRatingError, InvalidEmailError
from domain.value_objects.location import Location
from domain.value_objects.money import Money
from domain.value_objects.rating import Rating
from domain.value_objects.work_radius import WorkRadius


def make_client(**overrides) -> Client:
    defaults = dict(id="c1", email="alice@example.com", _password_hash="h", full_name="Alice")
    defaults.update(overrides)
    return Client(**defaults)


def make_hiver(**overrides) -> Hiver:
    defaults = dict(id="h1", email="bob@example.com", _password_hash="h", full_name="Bob")
    defaults.update(overrides)
    return Hiver(**defaults)


class TestUserBase:
    def test_user_is_abstract(self):
        with pytest.raises(TypeError):
            User(id="x", email="x@y.com", _password_hash="h", full_name="X")  # type: ignore[abstract]

    def test_invalid_email_rejected(self):
        with pytest.raises(InvalidEmailError):
            make_client(email="not-an-email")

    def test_deactivate(self):
        c = make_client()
        c.deactivate()
        assert c.is_active is False

    def test_password_hash_property(self):
        assert make_client(_password_hash="secret").password_hash == "secret"


class TestClient:
    def test_role_and_commission(self):
        c = make_client()
        assert c.get_role() == "client"
        assert c.calculate_commission(Money.of(100)) == Money.of(7)

    def test_can_post_task_with_good_rating(self):
        assert make_client().can_post_task() is True

    def test_low_rating_cannot_post(self):
        c = make_client(rating_as_client=Rating(1.5))
        assert c.can_post_task() is False
        with pytest.raises(InsufficientRatingError):
            c.assert_can_post_task()

    def test_update_rating_rolling_average(self):
        c = make_client(rating_as_client=Rating(4.0), review_count=1)
        c.update_rating(5.0)
        assert c.rating_as_client.value == 4.5
        assert c.review_count == 2


class TestHiver:
    def test_role(self):
        assert make_hiver().get_role() == "hiver"

    @pytest.mark.parametrize(
        "level,expected",
        [("beginner", 20), ("experienced", 18), ("master", 16), ("legend", 14)],
    )
    def test_commission_by_level(self, level, expected):
        h = make_hiver(level=level)
        assert h.calculate_commission(Money.of(100)) == Money.of(expected)

    @pytest.mark.parametrize(
        "xp,expected_level",
        [(0, "beginner"), (100, "experienced"), (500, "master"), (1500, "legend")],
    )
    def test_level_up_thresholds(self, xp, expected_level):
        h = make_hiver()
        h.add_xp(xp)
        assert h.level == expected_level

    def test_update_rating_awards_xp_and_counts_completion(self):
        h = make_hiver()
        h.update_rating(5.0)
        assert h.review_count == 1
        assert h.completed_tasks == 1
        assert h.xp_points == 10

    def test_toggle_availability(self):
        h = make_hiver()
        assert h.is_available_now is False
        h.toggle_availability()
        assert h.is_available_now is True

    def test_is_within_radius(self):
        sofia = Location(42.6977, 23.3219)
        nearby = Location(42.70, 23.33)
        h = make_hiver(location=sofia, work_radius=WorkRadius(5))
        assert h.is_within_radius(nearby) is True

    def test_is_within_radius_false_without_location(self):
        assert make_hiver().is_within_radius(Location(42.0, 23.0)) is False
