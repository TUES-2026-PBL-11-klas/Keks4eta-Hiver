"""Unit tests for OAuthLoginUseCase with in-memory fake repositories.

Application code imports as `from src.application...`, so this test puts the
`backend/` dir on sys.path and provides the env vars `Settings()` requires
(it is imported transitively via src.shared.security).
"""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://t:t@localhost/t")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

import pytest  # noqa: E402

from src.application.dtos.auth_dtos import OAuthUserInfo  # noqa: E402
from src.application.use_cases.auth.oauth_login_use_case import (  # noqa: E402
    OAuthLoginUseCase,
)
from src.domain.entities.user import Client, Hiver  # noqa: E402
from src.shared.security import decode_token  # noqa: E402


class FakeRepo:
    """Duck-typed stand-in for IClient/IHiverRepository (only what the use case calls)."""

    def __init__(self) -> None:
        self.saved: list = []

    async def find_by_oauth(self, provider: str, oauth_id: str):
        for u in self.saved:
            if u.oauth_provider == provider and u.oauth_id == oauth_id:
                return u
        return None

    async def find_by_email(self, email: str):
        for u in self.saved:
            if u.email == email:
                return u
        return None

    async def find_by_id(self, user_id: str):
        for u in self.saved:
            if u.id == user_id:
                return u
        return None

    async def save(self, entity):
        if entity not in self.saved:
            self.saved.append(entity)
        return entity


def info(**overrides) -> OAuthUserInfo:
    defaults = dict(
        provider="google",
        oauth_id="g-123",
        email="new@example.com",
        full_name="New User",
        role="client",
    )
    defaults.update(overrides)
    return OAuthUserInfo(**defaults)


@pytest.fixture
def repos():
    return FakeRepo(), FakeRepo()  # client_repo, hiver_repo


class TestOAuthLogin:
    async def test_new_account_creates_both_facets(self, repos):
        client_repo, hiver_repo = repos
        tokens = await OAuthLoginUseCase(client_repo, hiver_repo).execute(info())

        # Unified accounts: a brand-new social account gets BOTH a client and a
        # hiver profile sharing one user id; the role param is ignored.
        assert len(client_repo.saved) == 1
        assert len(hiver_repo.saved) == 1
        client_created = client_repo.saved[0]
        hiver_created = hiver_repo.saved[0]
        assert isinstance(client_created, Client)
        assert isinstance(hiver_created, Hiver)
        assert client_created.id == hiver_created.id
        assert client_created.oauth_provider == "google"
        assert client_created.password_hash is None  # passwordless account
        assert decode_token(tokens.access_token)["role"] == "client"

    async def test_role_param_is_ignored_both_facets_created(self, repos):
        client_repo, hiver_repo = repos
        await OAuthLoginUseCase(client_repo, hiver_repo).execute(
            info(role="hiver", oauth_id="g-999", email="both@example.com")
        )
        # Even with role="hiver", both facets are created (role is vestigial).
        assert len(client_repo.saved) == 1
        assert len(hiver_repo.saved) == 1

    async def test_logs_in_existing_oauth_identity_without_duplicating(self, repos):
        client_repo, hiver_repo = repos
        existing = Client(
            id="c-1", email="a@b.com", _password_hash=None, full_name="A",
            oauth_provider="google", oauth_id="g-123",
        )
        client_repo.saved.append(existing)

        await OAuthLoginUseCase(client_repo, hiver_repo).execute(
            info(oauth_id="g-123", email="a@b.com")
        )
        assert len(client_repo.saved) == 1  # no new account

    async def test_links_provider_to_existing_password_account(self, repos):
        client_repo, hiver_repo = repos
        existing = Client(
            id="c-1", email="dup@b.com", _password_hash="bcrypt-hash", full_name="Dup",
        )
        client_repo.saved.append(existing)

        await OAuthLoginUseCase(client_repo, hiver_repo).execute(
            info(oauth_id="g-555", email="dup@b.com")
        )
        assert len(client_repo.saved) == 1
        assert existing.oauth_provider == "google"
        assert existing.oauth_id == "g-555"
        assert existing.password_hash == "bcrypt-hash"  # password still works too
