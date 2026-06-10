from slowapi import Limiter
from slowapi.util import get_remote_address

from src.shared.config import settings

# Rate-limit counters live in **Redis** so the limits hold across multiple backend
# instances and survive a worker restart (a per-IP counter that expires after the
# window is exactly what Redis is good at). If Redis is unreachable — e.g. a teammate
# runs the API without the redis container — slowapi degrades to an in-memory store so
# the app still works; limits then apply per process instead of cluster-wide.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=settings.redis_url,
    in_memory_fallback_enabled=True,
    key_prefix="hiver-rl",
)
