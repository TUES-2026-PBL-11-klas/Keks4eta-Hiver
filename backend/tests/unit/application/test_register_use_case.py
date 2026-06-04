"""Unit tests for RegisterUseCase — unified accounts create BOTH facets."""
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

from src.application.dtos.auth_dtos import RegisterRequest  # noqa: E402
from src.application.use_cases.auth.register_use_case import RegisterUseCase  # noqa: E402
from src.domain.entities.user import Client, Hiver  # noqa: E402
from src.domain.errors.domain_errors import DuplicateEmailError  # noqa: E402
from src.shared.security import decode_token  # noqa: E402


class FakeRepo:
    def __init__(self) -> None:
        self.saved: list = []

    async def find_by_email(self, email: str):
        return next((u for u in self.saved if u.email == email), None)

    async def save(self, entity):
        if entity not in self.saved:
            self.saved.append(entity)
        return entity


@pytest.fixture
def repos():
    return FakeRepo(), FakeRepo()  # client_repo, hiver_repo


class TestRegister:
    async def test_creates_both_client_and_hiver(self, repos):
        client_repo, hiver_repo = repos
        tokens = await RegisterUseCase(client_repo, hiver_repo).execute(
            RegisterRequest(full_name="Maria Ivanova", email="m@example.com", password="supersecret")
        )

        assert len(client_repo.saved) == 1
        assert len(hiver_repo.saved) == 1
        assert isinstance(client_repo.saved[0], Client)
        assert isinstance(hiver_repo.saved[0], Hiver)
        # Both facets share one user id.
        assert client_repo.saved[0].id == hiver_repo.saved[0].id
        assert decode_token(tokens.access_token)["sub"] == client_repo.saved[0].id

    async def test_duplicate_email_rejected(self, repos):
        client_repo, hiver_repo = repos
        client_repo.saved.append(
            Client(id="c1", email="dup@example.com", _password_hash="h", full_name="Dup")
        )
        with pytest.raises(DuplicateEmailError):
            await RegisterUseCase(client_repo, hiver_repo).execute(
                RegisterRequest(full_name="X", email="dup@example.com", password="supersecret")
            )
