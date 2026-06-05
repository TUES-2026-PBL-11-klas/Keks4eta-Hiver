"""Unit tests for the Phase 4 profile use cases (edit profile + avatar upload)."""

import os
import sys
from io import BytesIO
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
from pydantic import ValidationError

from src.application.dtos.user_dtos import UpdateMeRequest
from src.application.use_cases.users.update_profile_use_case import UpdateProfileUseCase
from src.application.use_cases.users.upload_avatar_use_case import UploadAvatarUseCase
from src.domain.entities.user import Hiver
from src.domain.errors.domain_errors import (
    BusinessRuleViolationError,
    HiverNotFoundError,
)
from src.domain.value_objects.location import Location
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.work_radius import WorkRadius


def _valid_png() -> bytes:
    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (4, 4), (238, 127, 34)).save(buf, format="PNG")
    return buf.getvalue()


class FakeHiverRepo:
    def __init__(self, hiver: Hiver | None = None) -> None:
        self.hiver = hiver
        self.saved: Hiver | None = None

    async def find_by_id(self, hiver_id: str) -> Hiver | None:
        return self.hiver if self.hiver and self.hiver.id == hiver_id else None

    async def save(self, hiver: Hiver) -> Hiver:
        self.saved = hiver
        self.hiver = hiver
        return hiver


class FakeStoragePort:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    async def upload(
        self, bucket: str, key: str, data: bytes, content_type: str
    ) -> str:
        self.calls.append((bucket, key))
        return f"https://storage.example.com/{bucket}/{key}"

    async def delete(self, bucket: str, key: str) -> None: ...

    async def get_signed_url(
        self, bucket: str, key: str, expires_in: int = 3600
    ) -> str:
        return f"https://storage.example.com/{bucket}/{key}?signed=1"


def make_hiver(hid: str = "u-1") -> Hiver:
    return Hiver(
        id=hid,
        email="u@test.com",
        _password_hash=None,
        full_name="Old Name",
        bio="old bio",
        avg_rating=Rating(4.0),
        work_radius=WorkRadius(5),
        skills=["Cleaning"],
    )


# ── UpdateProfileUseCase ───────────────────────────────────────────────────────


class TestUpdateProfileUseCase:
    async def test_applies_all_fields(self):
        repo = FakeHiverRepo(make_hiver())
        req = UpdateMeRequest(
            full_name="New Name",
            phone="+359888",
            bio="new bio",
            skills=["Plumbing", "Tutoring"],
            work_radius_km=10,
            latitude=42.7,
            longitude=23.3,
            location_display="Sofia",
        )
        result = await UpdateProfileUseCase(repo).execute("u-1", req)

        assert result.full_name == "New Name"
        assert result.phone == "+359888"
        assert result.bio == "new bio"
        assert result.skills == ["Plumbing", "Tutoring"]
        assert result.work_radius == WorkRadius(10)
        assert result.location == Location(42.7, 23.3, "Sofia")
        assert repo.saved is result

    async def test_partial_update_leaves_other_fields(self):
        repo = FakeHiverRepo(make_hiver())
        result = await UpdateProfileUseCase(repo).execute(
            "u-1", UpdateMeRequest(bio="just the bio")
        )
        assert result.bio == "just the bio"
        assert result.full_name == "Old Name"  # untouched
        assert result.skills == ["Cleaning"]  # untouched
        assert result.location is None  # no coords sent → not set

    async def test_can_clear_bio_with_empty_string(self):
        repo = FakeHiverRepo(make_hiver())
        result = await UpdateProfileUseCase(repo).execute(
            "u-1", UpdateMeRequest(bio="")
        )
        assert result.bio == ""

    async def test_missing_hiver_raises(self):
        repo = FakeHiverRepo(None)
        with pytest.raises(HiverNotFoundError):
            await UpdateProfileUseCase(repo).execute("ghost", UpdateMeRequest(bio="x"))


# ── UpdateMeRequest validation ─────────────────────────────────────────────────


class TestUpdateMeRequestValidation:
    def test_rejects_disallowed_radius(self):
        with pytest.raises(ValidationError):
            UpdateMeRequest(work_radius_km=7)

    def test_accepts_allowed_radius(self):
        assert UpdateMeRequest(work_radius_km=15).work_radius_km == 15

    def test_requires_both_coordinates(self):
        with pytest.raises(ValidationError):
            UpdateMeRequest(latitude=42.7)  # longitude missing

    def test_rejects_out_of_range_latitude(self):
        with pytest.raises(ValidationError):
            UpdateMeRequest(latitude=120.0, longitude=23.0)

    def test_empty_request_is_valid(self):
        assert UpdateMeRequest().full_name is None


# ── UploadAvatarUseCase ────────────────────────────────────────────────────────


class TestUploadAvatarUseCase:
    async def test_uploads_and_sets_avatar_url(self):
        repo = FakeHiverRepo(make_hiver())
        storage = FakeStoragePort()
        url = await UploadAvatarUseCase(repo, storage).execute(
            "u-1", _valid_png(), "image/png"
        )
        assert "storage.example.com/avatars/" in url
        assert repo.saved is not None
        assert repo.saved.avatar_url == url
        assert storage.calls[0][0] == "avatars"

    async def test_rejects_non_image(self):
        repo = FakeHiverRepo(make_hiver())
        with pytest.raises(BusinessRuleViolationError):
            await UploadAvatarUseCase(repo, FakeStoragePort()).execute(
                "u-1", b"hello", "text/plain"
            )

    async def test_rejects_corrupt_image(self):
        repo = FakeHiverRepo(make_hiver())
        with pytest.raises(BusinessRuleViolationError):
            await UploadAvatarUseCase(repo, FakeStoragePort()).execute(
                "u-1", b"\x89PNG\r\n\x1a\n garbage", "image/png"
            )

    async def test_missing_hiver_raises(self):
        repo = FakeHiverRepo(None)
        with pytest.raises(HiverNotFoundError):
            await UploadAvatarUseCase(repo, FakeStoragePort()).execute(
                "ghost", _valid_png(), "image/png"
            )
