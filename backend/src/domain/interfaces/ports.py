from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.value_objects.money import Money

# ── Payment Port (Adapter pattern target) ───────────────────────────────────

class IPaymentPort(ABC):
    """
    Adapter Pattern: abstracts payment provider (Stripe, PayPal, etc.).
    Use cases depend on this interface, never on Stripe SDK directly.
    SOLID D: Dependency Inversion — high-level module depends on abstraction.
    """

    @abstractmethod
    async def hold_payment(self, amount: Money, customer_id: str) -> str:
        """Capture funds into escrow. Returns payment intent ID."""
        ...

    @abstractmethod
    async def release_payment(self, payment_intent_id: str) -> None:
        """Release held funds to hiver."""
        ...

    @abstractmethod
    async def refund_payment(self, payment_intent_id: str, amount: Money) -> None:
        """Refund captured funds to client."""
        ...

    @abstractmethod
    async def create_customer(self, email: str, name: str) -> str:
        """Create a provider-side customer. Returns customer ID."""
        ...


# ── Notification Port ────────────────────────────────────────────────────────

@dataclass
class NotificationPayload:
    recipient_id: str
    title: str
    body: str
    data: dict


class INotificationPort(ABC):
    """
    Abstracts push notification provider (Firebase FCM, APNs, etc.).
    SOLID D: use cases call this interface, not Firebase directly.
    """

    @abstractmethod
    async def send(self, payload: NotificationPayload) -> None: ...

    @abstractmethod
    async def send_bulk(self, payloads: list[NotificationPayload]) -> list[bool]: ...


# ── Storage Port ─────────────────────────────────────────────────────────────

class IStoragePort(ABC):
    """
    Abstracts object storage (Supabase Storage, Cloudflare R2, S3).
    """

    @abstractmethod
    async def upload(self, bucket: str, key: str, data: bytes, content_type: str) -> str:
        """Upload file. Returns public URL."""
        ...

    @abstractmethod
    async def delete(self, bucket: str, key: str) -> None: ...

    @abstractmethod
    async def get_signed_url(self, bucket: str, key: str, expires_in: int = 3600) -> str: ...


# ── Email Port ────────────────────────────────────────────────────────────────

@dataclass
class EmailPayload:
    to: str
    subject: str
    html_body: str
    text_body: str | None = None


class IEmailPort(ABC):
    """Abstracts transactional email provider (SendGrid, Resend, SES)."""

    @abstractmethod
    async def send(self, payload: EmailPayload) -> None: ...


# ── Geo Port ──────────────────────────────────────────────────────────────────

@dataclass
class GeocodingResult:
    latitude: float
    longitude: float
    display_address: str
    city: str | None = None
    country: str | None = None


class IGeoPort(ABC):
    """Abstracts geocoding provider (Google Maps, Mapbox, etc.)."""

    @abstractmethod
    async def geocode(self, address: str) -> GeocodingResult | None: ...

    @abstractmethod
    async def reverse_geocode(self, lat: float, lng: float) -> GeocodingResult | None: ...
