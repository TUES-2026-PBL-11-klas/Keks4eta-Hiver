from __future__ import annotations

from src.domain.interfaces.ports import IStoragePort
from src.infrastructure.storage.supabase_storage_adapter import SupabaseStorageAdapter
from src.shared.config import settings

# All task images live in this public bucket.
TASK_IMAGES_BUCKET = "task-images"


def get_storage_port() -> IStoragePort | None:
    """
    Return the Supabase storage adapter when configured, else None so callers can
    return a clean 503 ("image uploads not configured") instead of crashing.
    """
    if settings.supabase_url and settings.supabase_service_key:
        return SupabaseStorageAdapter(
            settings.supabase_url, settings.supabase_service_key
        )
    return None
