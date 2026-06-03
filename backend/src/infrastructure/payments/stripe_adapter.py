from __future__ import annotations

from domain.interfaces.ports import IPaymentPort
from domain.value_objects.money import Money


class StripeAdapter(IPaymentPort):
    """
    Adapter Pattern: adapts Stripe SDK to IPaymentPort interface.

    Why: use cases call IPaymentPort — if we swap to PayPal tomorrow,
    only this file changes, nothing in the application layer.
    OOP: Encapsulates all Stripe-specific details (cents conversion, API calls).
    """

    def __init__(self, stripe_client) -> None:
        self._stripe = stripe_client

    async def hold_payment(self, amount: Money, customer_id: str) -> str:
        """Capture funds into escrow via Stripe PaymentIntent (manual capture)."""
        intent = await self._stripe.payment_intents.create_async(
            amount=int(amount.value * 100),  # Stripe uses smallest currency unit
            currency=amount.currency.lower(),
            customer=customer_id,
            capture_method="manual",  # hold without capturing = simulated escrow
        )
        return intent.id

    async def release_payment(self, payment_intent_id: str) -> None:
        """Capture the held PaymentIntent — money moves to connected account."""
        await self._stripe.payment_intents.capture_async(payment_intent_id)

    async def refund_payment(self, payment_intent_id: str, amount: Money) -> None:
        """Issue a full or partial refund."""
        await self._stripe.refunds.create_async(
            payment_intent=payment_intent_id,
            amount=int(amount.value * 100),
        )

    async def create_customer(self, email: str, name: str) -> str:
        customer = await self._stripe.customers.create_async(email=email, name=name)
        return customer.id
