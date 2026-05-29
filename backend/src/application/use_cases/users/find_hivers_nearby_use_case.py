from src.domain.interfaces.repositories import IHiverRepository
from src.domain.value_objects.location import Location
from src.application.dtos.user_dtos import HiverSearchResult


class FindHiversNearbyUseCase:
    """
    Geo-search for available hivers via PostGIS stored function.
    OOP: Strategy — repository hides the PostGIS query; use case orchestrates.
    """

    def __init__(self, hiver_repo: IHiverRepository) -> None:
        self._hiver_repo = hiver_repo

    async def execute(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 10.0,
        vertical: str | None = None,
    ) -> list[HiverSearchResult]:
        origin = Location(latitude=latitude, longitude=longitude)
        hivers = await self._hiver_repo.find_available_near(
            location=origin, radius_km=radius_km, vertical=vertical
        )
        results: list[HiverSearchResult] = []
        for h in hivers:
            distance = (
                origin.distance_to_km(h.location) if h.location else None
            )
            results.append(
                HiverSearchResult(
                    user_id=h.id,
                    full_name=h.full_name,
                    avatar_url=h.avatar_url,
                    avg_rating=float(h.avg_rating.value),
                    level=h.level,
                    completed_tasks=h.completed_tasks,
                    is_available_now=h.is_available_now,
                    work_radius_km=h.work_radius.km,
                    distance_km=distance,
                )
            )
        return results
