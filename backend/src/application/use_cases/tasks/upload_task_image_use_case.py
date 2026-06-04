import uuid
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from src.application.dtos.task_dtos import TaskDetailResponse
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.domain.errors.domain_errors import (
    BusinessRuleViolationError,
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.interfaces.ports import IStoragePort
from src.domain.interfaces.repositories import ITaskRepository

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_IMAGES = 6
BUCKET = "task-images"


class UploadTaskImageUseCase:
    """Owner uploads an image to their task; stored in Supabase, URL appended."""

    def __init__(self, task_repo: ITaskRepository, storage_port: IStoragePort) -> None:
        self._task_repo = task_repo
        self._storage = storage_port

    async def execute(
        self, task_id: str, client_id: str, data: bytes, content_type: str
    ) -> TaskDetailResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if task.client_id != client_id:
            raise UnauthorizedActionError("add images to this task")

        ctype = (content_type or "").split(";")[0].strip().lower()
        ext = ALLOWED_TYPES.get(ctype)
        if ext is None:
            raise BusinessRuleViolationError(
                "Only JPEG, PNG, WebP or GIF images are allowed", "INVALID_IMAGE_TYPE"
            )
        if not data:
            raise BusinessRuleViolationError("Empty image", "EMPTY_IMAGE")
        if len(data) > MAX_BYTES:
            raise BusinessRuleViolationError(
                "Image too large (max 5 MB)", "IMAGE_TOO_LARGE"
            )
        if len(task.image_urls) >= MAX_IMAGES:
            raise BusinessRuleViolationError(
                f"A task can have at most {MAX_IMAGES} images", "TOO_MANY_IMAGES"
            )
        self._assert_decodable(data)

        key = f"{task_id}/{uuid.uuid4().hex}{ext}"
        url = await self._storage.upload(BUCKET, key, data, ctype)

        task.image_urls.append(url)
        await self._task_repo.save(task)
        return await GetTaskUseCase(self._task_repo).execute(task_id)

    @staticmethod
    def _assert_decodable(data: bytes) -> None:
        """Reject corrupt or truncated images before they reach storage.

        ``verify()`` catches structural corruption; a second ``load()`` on a
        fresh stream catches truncation that only surfaces during full decode
        (verify leaves the file object unusable, so we must re-open).
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
