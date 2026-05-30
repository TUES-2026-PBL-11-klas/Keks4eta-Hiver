import pytest

from domain.entities.offer import Offer, OfferStatus
from domain.errors.domain_errors import UnauthorizedActionError
from domain.value_objects.money import Money


def make_offer(**overrides) -> Offer:
    defaults = dict(
        id="o1",
        task_id="t1",
        hiver_id="h1",
        price=Money.of(100),
        message="I can do it",
        estimated_hours=3.0,
    )
    defaults.update(overrides)
    return Offer(**defaults)


class TestOfferLifecycle:
    def test_defaults_to_pending(self):
        assert make_offer().is_pending()

    def test_client_accepts(self):
        offer = make_offer()
        offer.accept(client_id_acting="c1", task_client_id="c1")
        assert offer.status == OfferStatus.ACCEPTED

    def test_only_task_owner_can_accept(self):
        offer = make_offer()
        with pytest.raises(UnauthorizedActionError):
            offer.accept(client_id_acting="intruder", task_client_id="c1")

    def test_only_task_owner_can_reject(self):
        offer = make_offer()
        with pytest.raises(UnauthorizedActionError):
            offer.reject(client_id_acting="intruder", task_client_id="c1")
        offer.reject(client_id_acting="c1", task_client_id="c1")
        assert offer.status == OfferStatus.REJECTED

    def test_only_owner_hiver_can_withdraw(self):
        offer = make_offer()
        with pytest.raises(UnauthorizedActionError):
            offer.withdraw("h2")
        offer.withdraw("h1")
        assert offer.status == OfferStatus.WITHDRAWN


class TestOfferMoney:
    def test_platform_fee_is_ten_percent(self):
        assert make_offer(price=Money.of(100)).platform_fee() == Money.of(10)

    def test_hiver_payout_is_net_of_fee(self):
        assert make_offer(price=Money.of(100)).hiver_payout() == Money.of(90)
