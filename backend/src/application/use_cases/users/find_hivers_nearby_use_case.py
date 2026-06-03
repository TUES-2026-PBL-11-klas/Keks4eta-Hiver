from src.application.dtos.user_dtos import HiverSearchResult
from src.domain.interfaces.repositories import IBoostRepository, IHiverRepository
from src.domain.value_objects.location import Location


class FindHiversNearbyUseCase:
    """
    Geo-search for available hivers via the PostGIS stored function.
    OOP: Strategy — repository hides the PostGIS query; use case orchestrates.
    Boosted hivers (active paid boost) are surfaced first, distance order within.
    """

    def __init__(
        self,
        hiver_repo: IHiverRepository,
        boost_repo: IBoostRepository | None = None,
    ) -> None:
        self._hiver_repo = hiver_repo
        self._boost_repo = boost_repo

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

        boosted_ids: set[str] = set()
        if self._boost_repo is not None:
            boosted_ids = await self._boost_repo.active_hiver_ids(vertical)

        results: list[HiverSearchResult] = []
        for h in hivers:
            distance = origin.distance_to_km(h.location) if h.location else None
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
                    latitude=h.location.latitude if h.location else None,
                    longitude=h.location.longitude if h.location else None,
                    distance_km=distance,
                    is_boosted=h.id in boosted_ids,
                )
            )

        # Stable sort: boosted first, preserving the repo's distance ordering within.
        results.sort(key=lambda r: not r.is_boosted)
        return results
