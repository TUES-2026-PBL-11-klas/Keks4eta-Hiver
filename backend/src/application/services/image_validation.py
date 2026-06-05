"""Shared upload-image validation (task images + profile avatars).

One source of truth for the rules every image upload must satisfy: an allowed
content type, a non-empty body within the size limit, and bytes that actually
decode (catching corrupt/truncated files before they reach storage).
"""

from io import BytesIO

from PIL import Image, UnidentifiedImageError

from src.domain.errors.domain_errors import BusinessRuleViolationError

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def validate_image(data: bytes, content_type: str, *, max_bytes: int) -> str:
    """Validate an uploaded image and return its canonical file extension.

    Raises ``BusinessRuleViolationError`` (HTTP 422) on any failure so callers
    never have to special-case the rejection reasons.
    """
    ctype = (content_type or "").split(";")[0].strip().lower()
    ext = ALLOWED_IMAGE_TYPES.get(ctype)
    if ext is None:
        raise BusinessRuleViolationError(
            "Only JPEG, PNG, WebP or GIF images are allowed", "INVALID_IMAGE_TYPE"
        )
    if not data:
        raise BusinessRuleViolationError("Empty image", "EMPTY_IMAGE")
    if len(data) > max_bytes:
        raise BusinessRuleViolationError(
            f"Image too large (max {max_bytes // (1024 * 1024)} MB)", "IMAGE_TOO_LARGE"
        )
    _assert_decodable(data)
    return ext


def _assert_decodable(data: bytes) -> None:
    """Reject corrupt or truncated images before they reach storage.

    ``verify()`` catches structural corruption; a second ``load()`` on a fresh
    stream catches truncation that only surfaces during full decode (verify
    leaves the file object unusable, so we must re-open).
    """
    try:
        with Image.open(BytesIO(data)) as img:
            img.verify()
        with Image.open(BytesIO(data)) as img:
            img.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise BusinessRuleViolationError(
            "Image is corrupt or truncated", "INVALID_IMAGE"
        ) from exc
