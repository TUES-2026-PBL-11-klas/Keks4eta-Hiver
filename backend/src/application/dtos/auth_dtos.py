from pydantic import BaseModel, EmailStr, field_validator
from typing import Literal


class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    # Unified accounts: every account is both client and hiver, so role is no
    # longer chosen at registration. Kept optional + ignored for backward compat.
    role: Literal["client", "hiver"] | None = None
    phone: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OAuthUserInfo(BaseModel):
    """Normalized identity returned by a social provider after token exchange."""
    provider: Literal["google", "facebook"]
    oauth_id: str
    email: EmailStr
    full_name: str
    avatar_url: str | None = None
    role: Literal["client", "hiver"] = "client"  # role for first-time accounts


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    phone: str | None
    avatar_url: str | None
    is_active: bool

    model_config = {"from_attributes": True}
