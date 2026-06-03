import uuid

from src.application.dtos.boost_dtos import (
    BOOST_DURATION_DAYS,
    BOOST_PRICE_BGN,
    BoostResponse,
)
from src.domain.entities.boost import Boost
from src.domain.interfaces.ports import IPaymentPort
from src.domain.interfaces.repositories import IBoostRepository
from src.domain.value_objects.money import Money


def _to_response(b: Boost) -> BoostResponse:
    return BoostResponse(
        id=b.id,
        hiver_id=b.hiver_id,
        vertical=b.vertical,
        expires_at=b.expires_at,
        created_at=b.created_at,
        is_active=b.is_active(),
    )


class BuyBoostUseCase:
    """Hiver buys a visibility boost. Charged through the payment port (mock by
    default); a real Stripe charge would be a one-off PaymentIntent."""

    def __init__(
        self, boost_repo: IBoostRepository, payment_port: IPaymentPort
    ) -> None:
        self._boost_repo = boost_repo
        self._payment_port = payment_port

    async def execute(
        self, hiver_id: str, vertical: str | None = None
    ) -> BoostResponse:
        payment_id = await self._payment_port.hold_payment(
            Money.of(BOOST_PRICE_BGN), hiver_id
        )
        boost = await self._boost_repo.add(
            Boost.purchase(
                id=str(uuid.uuid4()),
                hiver_id=hiver_id,
                stripe_payment_id=payment_id,
                days=BOOST_DURATION_DAYS,
                vertical=vertical,
            )
        )
        return _to_response(boost)


class GetMyBoostUseCase:
    def __init__(self, boost_repo: IBoostRepository) -> None:
        self._boost_repo = boost_repo

    async def execute(self, hiver_id: str) -> BoostResponse | None:
        boost = await self._boost_repo.find_active_for_hiver(hiver_id)
        return _to_response(boost) if boost else None
