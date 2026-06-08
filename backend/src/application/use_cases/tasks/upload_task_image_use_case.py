import uuid

from src.application.dtos.task_dtos import TaskDetailResponse
from src.application.services.image_validation import validate_image
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.domain.errors.domain_errors import (
    BusinessRuleViolationError,
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.interfaces.ports import IStoragePort
from src.domain.interfaces.repositories import ITaskRepository

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
        if len(task.image_urls) >= MAX_IMAGES:
            raise BusinessRuleViolationError(
                f"A task can have at most {MAX_IMAGES} images", "TOO_MANY_IMAGES"
            )

        ext = validate_image(data, content_type, max_bytes=MAX_BYTES)
        ctype = (content_type or "").split(";")[0].strip().lower()
        key = f"{task_id}/{uuid.uuid4().hex}{ext}"
        url = await self._storage.upload(BUCKET, key, data, ctype)

        task.image_urls.append(url)
        await self._task_repo.save(task)
        return await GetTaskUseCase(self._task_repo).execute(task_id)


def _key_from_url(url: str) -> str | None:
    """Extract the storage object key from a public Supabase URL (…/public/<bucket>/<key>)."""
    marker = f"/public/{BUCKET}/"
    i = url.find(marker)
    return url[i + len(marker) :] if i != -1 else None


class DeleteTaskImageUseCase:
    """Owner removes one image from their task and (best-effort) from storage."""

    def __init__(self, task_repo: ITaskRepository, storage_port: IStoragePort | None) -> None:
        self._task_repo = task_repo
        self._storage = storage_port

    async def execute(self, task_id: str, client_id: str, url: str) -> TaskDetailResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if task.client_id != client_id:
            raise UnauthorizedActionError("remove images from this task")
        if url not in task.image_urls:
            raise BusinessRuleViolationError("image not found on this task", "IMAGE_NOT_FOUND")

        task.image_urls.remove(url)
        await self._task_repo.save(task)

        # Best-effort storage cleanup — the image is already off the task, so a failed
        # delete only leaves an orphaned object, which must not fail the user's action.
        key = _key_from_url(url)
        if self._storage is not None and key:
            try:
                await self._storage.delete(BUCKET, key)
            except Exception:  # noqa: BLE001 — orphan cleanup is non-critical
                pass

        return await GetTaskUseCase(self._task_repo).execute(task_id)
