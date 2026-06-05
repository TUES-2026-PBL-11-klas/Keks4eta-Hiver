from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from math import atan2, cos, radians, sin, sqrt

_executor = ThreadPoolExecutor(max_workers=4)


def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    CPU-intensive Haversine formula — runs in thread pool,
    not blocking the async event loop.
    Threading: offloads CPU work from async code.
    """
    R = 6_371_000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lng2 - lng1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


async def calculate_distances_async(
    center_lat: float,
    center_lng: float,
    points: list[tuple[float, float]],
) -> list[float]:
    """Non-blocking: runs Haversine in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        lambda: [
            _haversine_distance(center_lat, center_lng, lat, lng)
            for lat, lng in points
        ],
    )
