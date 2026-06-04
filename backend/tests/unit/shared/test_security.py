"""Unit tests for shared security utilities."""
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

from src.domain.errors.domain_errors import InvalidTokenError, TokenExpiredError
from src.shared.security import create_access_token, create_refresh_token, decode_token


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token("user-1", "client")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_payload_contains_sub_and_role(self):
        token = create_access_token("user-42", "hiver")
        payload = decode_token(token)
        assert payload["sub"] == "user-42"
        assert payload["role"] == "hiver"

    def test_two_tokens_differ(self):
        t1 = create_access_token("u1", "client")
        t2 = create_access_token("u2", "client")
        assert t1 != t2

    def test_client_role_in_token(self):
        token = create_access_token("c-1", "client")
        assert decode_token(token)["role"] == "client"


class TestCreateRefreshToken:
    def test_returns_string(self):
        token = create_refresh_token("user-1")
        assert isinstance(token, str)

    def test_payload_has_type_refresh(self):
        token = create_refresh_token("user-1")
        payload = decode_token(token)
        assert payload.get("type") == "refresh"
        assert payload["sub"] == "user-1"

    def test_no_role_in_refresh_token(self):
        token = create_refresh_token("user-1")
        payload = decode_token(token)
        assert "role" not in payload


class TestDecodeToken:
    def test_decodes_valid_access_token(self):
        token = create_access_token("u-1", "client")
        payload = decode_token(token)
        assert payload["sub"] == "u-1"

    def test_decodes_valid_refresh_token(self):
        token = create_refresh_token("u-2")
        payload = decode_token(token)
        assert payload["sub"] == "u-2"

    def test_invalid_token_raises(self):
        with pytest.raises(InvalidTokenError):
            decode_token("not.a.valid.jwt")

    def test_tampered_token_raises(self):
        token = create_access_token("u-1", "client")
        parts = token.split(".")
        parts[1] = "tampered"
        with pytest.raises(InvalidTokenError):
            decode_token(".".join(parts))

    def test_expired_token_raises(self):
        from datetime import datetime, timedelta

        from jose import jwt

        from src.shared.config import settings

        payload = {
            "sub": "u-1",
            "role": "client",
            "exp": datetime.utcnow() - timedelta(seconds=1),
        }
        expired_token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(TokenExpiredError):
            decode_token(expired_token)
