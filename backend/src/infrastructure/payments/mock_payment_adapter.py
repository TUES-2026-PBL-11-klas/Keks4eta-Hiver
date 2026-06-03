from __future__ import annotations
import uuid

from domain.interfaces.ports import IPaymentPort
from domain.value_objects.money import Money


class MockPaymentAdapter(IPaymentPort):
    """
    Functional in-app escrow — no external Stripe account required.

    Implements the exact same IPaymentPort the real StripeAdapter does, so the
    application layer is byte-for-byte identical whether we run mock or real.
    Hold / release / refund move *real database rows* (the Transaction entity);
    only the external money movement is simulated. Swap to StripeAdapter via
    payment_factory.get_payment_port once test keys exist — zero use-case change
    (Liskov substitution + the Adapter pattern doing its job).
    """

    async def hold_payment(self, amount: Money, customer_id: str) -> str:
        # Mirror Stripe's "pi_..." PaymentIntent id shape so logs/UX read the same.
        return f"pi_mock_{uuid.uuid4().hex[:24]}"

    async def release_payment(self, payment_intent_id: str) -> None:
        return None

    async def refund_payment(self, payment_intent_id: str, amount: Money) -> None:
        return None

    async def create_customer(self, email: str, name: str) -> str:
        return f"cus_mock_{uuid.uuid4().hex[:24]}"
