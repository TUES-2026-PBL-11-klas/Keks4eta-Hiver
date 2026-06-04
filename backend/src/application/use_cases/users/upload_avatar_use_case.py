import uuid

from src.application.services.image_validation import validate_image
from src.domain.errors.domain_errors import HiverNotFoundError
from src.domain.interfaces.ports import IStoragePort
from src.domain.interfaces.repositories import IHiverRepository

MAX_BYTES = 3 * 1024 * 1024  # 3 MB — avatars are small
BUCKET = "avatars"


class UploadAvatarUseCase:
    """Validate and store a profile avatar, then point the account at its URL.

    Avatars are shared user data, so saving via the hiver facet updates the
    underlying user row (and therefore the client facet too).
    """

    def __init__(
        self, hiver_repo: IHiverRepository, storage_port: IStoragePort
    ) -> None:
        self._hiver_repo = hiver_repo
        self._storage = storage_port

    async def execute(self, user_id: str, data: bytes, content_type: str) -> str:
        ext = validate_image(data, content_type, max_bytes=MAX_BYTES)
        hiver = await self._hiver_repo.find_by_id(user_id)
        if hiver is None:
            raise HiverNotFoundError(user_id)

        ctype = (content_type or "").split(";")[0].strip().lower()
        key = f"{user_id}/{uuid.uuid4().hex}{ext}"
        url = await self._storage.upload(BUCKET, key, data, ctype)

        hiver.avatar_url = url
        await self._hiver_repo.save(hiver)
        return url
