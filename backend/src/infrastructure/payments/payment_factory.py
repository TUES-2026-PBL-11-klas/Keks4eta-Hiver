from __future__ import annotations

from src.domain.interfaces.ports import IPaymentPort
from src.infrastructure.payments.mock_payment_adapter import MockPaymentAdapter
from src.shared.config import settings


def _is_real_stripe_key(key: str) -> bool:
    """A genuine Stripe secret key — not one of our dummy/placeholder stand-ins."""
    return key.startswith("sk_") and not any(
        marker in key for marker in ("dummy", "placeholder")
    )


def get_payment_port() -> IPaymentPort:
    """
    Hybrid adapter selection: use the real Stripe adapter only when a genuine
    secret key is configured; otherwise fall back to the functional mock so the
    whole escrow flow (hold on accept, release, refund on cancel) works
    end-to-end with no external account. This is the single line you change to
    go live — nothing in the application layer knows which adapter it got.
    """
    key = settings.stripe_secret_key or ""
    if _is_real_stripe_key(key):
        try:
            import stripe

            from src.infrastructure.payments.stripe_adapter import StripeAdapter

            return StripeAdapter(stripe.StripeClient(key))
        except Exception:
            # A misconfigured real key must not break the app — degrade to mock.
            return MockPaymentAdapter()
    return MockPaymentAdapter()
