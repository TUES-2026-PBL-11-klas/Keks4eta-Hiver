"""Unit tests for auth use cases (login, register, refresh)."""
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

import pytest

from src.application.dtos.auth_dtos import LoginRequest, RefreshRequest, RegisterRequest
from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.auth.register_use_case import RegisterUseCase
from src.domain.entities.user import Client, Hiver
from src.domain.errors.domain_errors import (
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from src.shared.password import hash_password
from src.shared.security import create_refresh_token, decode_token


class FakeUserRepo:
    def __init__(self) -> None:
        self.saved: list = []

    async def find_by_email(self, email: str):
        return next((u for u in self.saved if u.email == email), None)

    async def find_by_id(self, user_id: str):
        return next((u for u in self.saved if u.id == user_id), None)

    async def find_by_oauth(self, provider: str, oauth_id: str):
        return None

    async def save(self, entity):
        if entity not in self.saved:
            self.saved.append(entity)
        return entity


class TestLoginUseCase:
    async def test_login_existing_client(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        pw = hash_password("secret")
        repo_c.saved.append(Client(id="c1", email="a@b.com", _password_hash=pw, full_name="A"))

        tokens = await LoginUseCase(repo_c, repo_h).execute(
            LoginRequest(email="a@b.com", password="secret")
        )
        assert decode_token(tokens.access_token)["role"] == "client"

    async def test_login_existing_hiver(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        pw = hash_password("password1")
        repo_h.saved.append(Hiver(id="h1", email="hiver@x.com", _password_hash=pw, full_name="H"))

        tokens = await LoginUseCase(repo_c, repo_h).execute(
            LoginRequest(email="hiver@x.com", password="password1")
        )
        assert decode_token(tokens.access_token)["role"] == "hiver"

    async def test_login_wrong_password_raises(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        pw = hash_password("right")
        repo_c.saved.append(Client(id="c1", email="a@b.com", _password_hash=pw, full_name="A"))

        with pytest.raises(InvalidCredentialsError):
            await LoginUseCase(repo_c, repo_h).execute(
                LoginRequest(email="a@b.com", password="wrong")
            )

    async def test_login_unknown_email_raises(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        with pytest.raises(InvalidCredentialsError):
            await LoginUseCase(repo_c, repo_h).execute(
                LoginRequest(email="ghost@x.com", password="x")
            )


class TestRegisterUseCase:
    async def test_register_client_creates_and_returns_tokens(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        tokens = await RegisterUseCase(repo_c, repo_h).execute(
            RegisterRequest(email="new@x.com", password="password1", full_name="New", role="client")
        )
        assert len(repo_c.saved) == 1
        assert isinstance(repo_c.saved[0], Client)
        assert decode_token(tokens.access_token)["role"] == "client"

    async def test_register_hiver_creates_hiver(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        await RegisterUseCase(repo_c, repo_h).execute(
            RegisterRequest(email="h@x.com", password="password1", full_name="Hiver", role="hiver")
        )
        assert len(repo_h.saved) == 1
        assert isinstance(repo_h.saved[0], Hiver)

    async def test_register_duplicate_email_raises(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        repo_c.saved.append(Client(id="c1", email="dup@x.com", _password_hash=None, full_name="X"))

        with pytest.raises(DuplicateEmailError):
            await RegisterUseCase(repo_c, repo_h).execute(
                RegisterRequest(email="dup@x.com", password="password1", full_name="Y", role="client")
            )

    async def test_register_duplicate_in_hiver_table_raises(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        repo_h.saved.append(Hiver(id="h1", email="dup@x.com", _password_hash=None, full_name="H"))

        with pytest.raises(DuplicateEmailError):
            await RegisterUseCase(repo_c, repo_h).execute(
                RegisterRequest(email="dup@x.com", password="password1", full_name="Y", role="client")
            )


class TestRefreshTokenUseCase:
    async def test_refresh_returns_new_tokens_for_client(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        user = Client(id="c1", email="a@b.com", _password_hash=None, full_name="A")
        repo_c.saved.append(user)

        refresh = create_refresh_token("c1")
        tokens = await RefreshTokenUseCase(repo_c, repo_h).execute(refresh)
        assert decode_token(tokens.access_token)["role"] == "client"

    async def test_refresh_returns_new_tokens_for_hiver(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        user = Hiver(id="h1", email="h@b.com", _password_hash=None, full_name="H")
        repo_h.saved.append(user)

        refresh = create_refresh_token("h1")
        tokens = await RefreshTokenUseCase(repo_c, repo_h).execute(refresh)
        assert decode_token(tokens.access_token)["role"] == "hiver"

    async def test_refresh_with_access_token_raises(self):
        from src.shared.security import create_access_token
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        access = create_access_token("c1", "client")

        with pytest.raises(InvalidTokenError):
            await RefreshTokenUseCase(repo_c, repo_h).execute(access)

    async def test_refresh_with_unknown_user_raises(self):
        repo_c, repo_h = FakeUserRepo(), FakeUserRepo()
        refresh = create_refresh_token("nobody")

        with pytest.raises(InvalidTokenError):
            await RefreshTokenUseCase(repo_c, repo_h).execute(refresh)
