from __future__ import annotations

import httpx
from domain.interfaces.ports import IStoragePort


class SupabaseStorageAdapter(IStoragePort):
    """
    Real object storage backed by Supabase Storage (S3-compatible REST API),
    reached with the service_role key. Implements the same IStoragePort an S3/R2
    adapter would, so swapping providers is a DI change only.
    """

    def __init__(self, base_url: str, service_key: str) -> None:
        self._base = base_url.rstrip("/")
        self._key = service_key

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self._key}", "apikey": self._key}
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    async def ensure_bucket(self, bucket: str, public: bool = True) -> None:
        """Create the bucket if it doesn't exist (idempotent)."""
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base}/storage/v1/bucket",
                headers=self._headers("application/json"),
                json={"id": bucket, "name": bucket, "public": public},
            )
        # 200 = created; 400/409 = already exists — both acceptable.
        if resp.status_code not in (200, 400, 409):
            resp.raise_for_status()

    async def upload(
        self, bucket: str, key: str, data: bytes, content_type: str
    ) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self._base}/storage/v1/object/{bucket}/{key}",
                headers={**self._headers(content_type), "x-upsert": "true"},
                content=data,
            )
            resp.raise_for_status()
        # Public bucket → stable public URL.
        return f"{self._base}/storage/v1/object/public/{bucket}/{key}"

    async def delete(self, bucket: str, key: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                "DELETE",
                f"{self._base}/storage/v1/object/{bucket}/{key}",
                headers=self._headers(),
            )
            resp.raise_for_status()

    async def get_signed_url(
        self, bucket: str, key: str, expires_in: int = 3600
    ) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self._base}/storage/v1/object/sign/{bucket}/{key}",
                headers=self._headers("application/json"),
                json={"expiresIn": expires_in},
            )
            resp.raise_for_status()
            signed = resp.json()["signedURL"]
        return f"{self._base}/storage/v1{signed}"
