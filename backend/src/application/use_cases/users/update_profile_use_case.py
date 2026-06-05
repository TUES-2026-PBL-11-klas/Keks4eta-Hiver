from src.application.dtos.user_dtos import UpdateMeRequest
from src.domain.entities.user import Hiver
from src.domain.errors.domain_errors import HiverNotFoundError
from src.domain.interfaces.repositories import IHiverRepository
from src.domain.value_objects.location import Location
from src.domain.value_objects.work_radius import WorkRadius


class UpdateProfileUseCase:
    """Apply a partial profile edit to the signed-in account.

    Editable fields live on the hiver facet (bio, skills, work radius, service
    location) plus the shared user row (full name, phone) — and the hiver
    repository writes both, so a single save covers the whole edit. PATCH
    semantics: only the fields actually present in the request are changed.
    """

    def __init__(self, hiver_repo: IHiverRepository) -> None:
        self._hiver_repo = hiver_repo

    async def execute(self, user_id: str, request: UpdateMeRequest) -> Hiver:
        hiver = await self._hiver_repo.find_by_id(user_id)
        if hiver is None:
            raise HiverNotFoundError(user_id)

        if request.full_name is not None:
            hiver.full_name = request.full_name
        if request.phone is not None:
            hiver.phone = request.phone
        if request.bio is not None:
            hiver.bio = request.bio
        if request.skills is not None:
            hiver.skills = request.skills
        if request.work_radius_km is not None:
            hiver.work_radius = WorkRadius(request.work_radius_km)
        if request.latitude is not None and request.longitude is not None:
            hiver.location = Location(
                latitude=request.latitude,
                longitude=request.longitude,
                display_address=request.location_display,
            )

        await self._hiver_repo.save(hiver)
        return hiver
