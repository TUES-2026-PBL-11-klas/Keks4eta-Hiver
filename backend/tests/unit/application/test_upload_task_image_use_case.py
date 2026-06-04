"""Unit tests for the image-integrity guard in UploadTaskImageUseCase.

Application code imports as `from src.application...`, so put `backend/` on
sys.path (mirrors test_oauth_login_use_case) and provide the env vars
`Settings()` needs (imported transitively).
"""
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

import pytest  # noqa: E402
from PIL import Image  # noqa: E402

from src.domain.errors.domain_errors import BusinessRuleViolationError  # noqa: E402
from src.application.use_cases.tasks.upload_task_image_use_case import (  # noqa: E402
    UploadTaskImageUseCase,
)


def _valid_png() -> bytes:
    buf = BytesIO()
    Image.new("RGB", (8, 8), (238, 127, 34)).save(buf, format="PNG")
    return buf.getvalue()


class TestImageIntegrityGuard:
    def test_valid_png_passes(self):
        UploadTaskImageUseCase._assert_decodable(_valid_png())  # no raise

    def test_garbage_bytes_rejected(self):
        with pytest.raises(BusinessRuleViolationError) as exc:
            UploadTaskImageUseCase._assert_decodable(b"this is not an image")
        assert exc.value.code == "INVALID_IMAGE"

    def test_truncated_png_rejected(self):
        with pytest.raises(BusinessRuleViolationError) as exc:
            UploadTaskImageUseCase._assert_decodable(_valid_png()[:20])
        assert exc.value.code == "INVALID_IMAGE"
