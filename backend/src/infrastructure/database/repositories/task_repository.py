from __future__ import annotations

import uuid

from geoalchemy2.elements import WKTElement
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.task import Task, TaskStatus
from src.domain.interfaces.repositories import ITaskRepository, PaginatedResult
from src.domain.value_objects.location import Location
from src.domain.value_objects.money import Money
from src.infrastructure.database.models import TaskModel


def _model_to_domain(
    m: TaskModel, coords: dict[str, tuple[float, float]] | None = None
) -> Task:
    # Real lat/lng come from the PostGIS `location_point` (read via ST_Y/ST_X in
    # `_coords_for`). `location_display` is only ever persisted alongside a point
    # (see `save`), so a missing entry here means the task genuinely has no
    # location — never fabricate (0, 0), which used to silently corrupt the map.
    location = None
    point = (coords or {}).get(m.id)
    if point is not None:
        location = Location(point[0], point[1], m.location_display)
    return Task(
        id=m.id,
        client_id=m.client_id,
        hiver_id=m.hiver_id,
        vertical=m.vertical,
        subcategory=m.subcategory,
        title=m.title,
        description=m.description,
        status=TaskStatus(m.status),
        budget_min=Money.of(m.budget_min) if m.budget_min else None,
        budget_max=Money.of(m.budget_max) if m.budget_max else None,
        is_urgent=m.is_urgent,
        location=location,
        smart_answers=m.smart_answers or {},
        image_urls=m.image_urls or [],
        expires_at=m.expires_at,
        featured_until=m.featured_until,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class PostgresTaskRepository(ITaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _coords_for(self, ids: list[str]) -> dict[str, tuple[float, float]]:
        """Batch-read real (lat, lng) for tasks with a PostGIS point.

        ST_Y/ST_X on the geometry cast avoid a shapely dependency (same trick
        the hiver repository uses), and one query keeps the read path free of
        N+1 lookups.
        """
        if not ids:
            return {}
        rows = await self._session.execute(
            text(
                """
                SELECT id,
                       ST_Y(location_point::geometry) AS lat,
                       ST_X(location_point::geometry) AS lng
                FROM tasks
                WHERE id = ANY(:ids) AND location_point IS NOT NULL
                """
            ),
            {"ids": ids},
        )
        return {r.id: (r.lat, r.lng) for r in rows}

    async def find_by_id(self, task_id: str) -> Task | None:
        model = await self._session.get(TaskModel, task_id)
        if model is None:
            return None
        coords = await self._coords_for([model.id])
        return _model_to_domain(model, coords)

    async def find_nearby(
        self, location: Location, radius_km: int, vertical: str | None = None
    ) -> list[Task]:
        query = text("""
            SELECT id FROM tasks
            WHERE status = 'open'
              AND location_point IS NOT NULL
              AND ST_DWithin(
                  location_point::geography,
                  ST_MakePoint(:lng, :lat)::geography,
                  :radius_m
              )
              AND (:vertical IS NULL OR vertical = :vertical)
            ORDER BY ST_Distance(location_point::geography,
                                 ST_MakePoint(:lng, :lat)::geography) ASC
            LIMIT 50
        """)
        result = await self._session.execute(
            query,
            {
                "lat": location.latitude,
                "lng": location.longitude,
                "radius_m": radius_km * 1000,
                "vertical": vertical,
            },
        )
        ids = [row.id for row in result]
        coords = await self._coords_for(ids)
        tasks = []
        for task_id in ids:
            model = await self._session.get(TaskModel, task_id)
            if model:
                tasks.append(_model_to_domain(model, coords))
        return tasks

    async def search(
        self,
        vertical: str | None = None,
        status: str | None = None,
        is_urgent: bool | None = None,
        min_budget: float | None = None,
        max_budget: float | None = None,
        q: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        radius_km: float | None = None,
        sort: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResult[Task]:
        filters = []
        if vertical is not None:
            filters.append(TaskModel.vertical == vertical)
        if status is not None:
            filters.append(TaskModel.status == status)
        if is_urgent is not None:
            filters.append(TaskModel.is_urgent == is_urgent)
        if min_budget is not None:
            filters.append(TaskModel.budget_max >= min_budget)
        if max_budget is not None:
            filters.append(TaskModel.budget_min <= max_budget)
        if q:
            like = f"%{q.strip()}%"
            filters.append(
                or_(
                    TaskModel.title.ilike(like),
                    TaskModel.description.ilike(like),
                    TaskModel.subcategory.ilike(like),
                )
            )

        # Geo radius filter (PostGIS). `location_point` is a geography column;
        # use the proven raw-SQL form `ST_MakePoint(lng,lat)::geography` (the
        # SRID-0 → 4326 cast that find_nearby relies on). geoalchemy2's typed
        # cast renders an invalid `geography(GEOMETRY,-1)` typmod, so avoid it.
        geo_active = lat is not None and lng is not None and radius_km is not None
        geo_clause = None
        if geo_active:
            # Narrow for the type checker — geo_active already guarantees these.
            assert lat is not None and lng is not None and radius_km is not None
            filters.append(TaskModel.location_point.isnot(None))
            geo_clause = text(
                "ST_DWithin(location_point, "
                "ST_MakePoint(:geo_lng, :geo_lat)::geography, :geo_radius_m)"
            ).bindparams(geo_lng=lng, geo_lat=lat, geo_radius_m=radius_km * 1000)

        count_q = select(func.count()).select_from(TaskModel)
        list_q = select(TaskModel)
        for f in filters:
            count_q = count_q.where(f)
            list_q = list_q.where(f)
        # The PostGIS predicate is a raw TextClause, applied apart from the ORM
        # column filters so the `filters` list stays uniformly typed.
        if geo_clause is not None:
            count_q = count_q.where(geo_clause)
            list_q = list_q.where(geo_clause)

        # Paid promotion wins first: currently-featured tasks are pinned to the
        # top regardless of the chosen sort, which then orders within each group.
        featured_first = (
            (TaskModel.featured_until.isnot(None)) & (TaskModel.featured_until > func.now())
        ).desc()
        if sort == "budget":
            list_q = list_q.order_by(
                featured_first, TaskModel.budget_max.desc().nullslast()
            )
        elif sort == "distance" and geo_active:
            list_q = list_q.order_by(
                featured_first,
                text(
                    "ST_Distance(location_point, "
                    "ST_MakePoint(:geo_olng, :geo_olat)::geography) ASC"
                ).bindparams(geo_olng=lng, geo_olat=lat),
            )
        else:  # "recent" / default
            list_q = list_q.order_by(featured_first, TaskModel.created_at.desc())

        total = (await self._session.execute(count_q)).scalar_one()
        result = await self._session.execute(
            list_q.offset((page - 1) * page_size).limit(page_size)
        )
        models = list(result.scalars())
        coords = await self._coords_for([m.id for m in models])
        items = [_model_to_domain(m, coords) for m in models]
        return PaginatedResult(items=items, total=total, page=page, page_size=page_size)

    async def find_by_client(
        self, client_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[Task]:
        count_result = await self._session.execute(
            select(func.count())
            .select_from(TaskModel)
            .where(TaskModel.client_id == client_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(TaskModel)
            .where(TaskModel.client_id == client_id)
            .order_by(TaskModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = list(result.scalars())
        coords = await self._coords_for([m.id for m in models])
        items = [_model_to_domain(m, coords) for m in models]
        return PaginatedResult(items=items, total=total, page=page, page_size=page_size)

    async def save(self, task: Task) -> Task:
        model = await self._session.get(TaskModel, task.id)
        if model is None:
            model = TaskModel(
                id=task.id or str(uuid.uuid4()),
                client_id=task.client_id,
                hiver_id=task.hiver_id,
                vertical=task.vertical,
                subcategory=task.subcategory,
                title=task.title,
                description=task.description,
                status=task.status.value,
                budget_min=float(task.budget_min.value) if task.budget_min else None,
                budget_max=float(task.budget_max.value) if task.budget_max else None,
                is_urgent=task.is_urgent,
                location_display=task.location.display_address
                if task.location
                else None,
                # Persist the PostGIS point (WGS 84) so geo-search can find the task.
                # POINT takes (longitude latitude) order. WKTElement avoids a shapely dep.
                location_point=WKTElement(
                    f"POINT({task.location.longitude} {task.location.latitude})",
                    srid=4326,
                )
                if task.location
                else None,
                smart_answers=task.smart_answers,
                image_urls=task.image_urls,
                expires_at=task.expires_at,
                featured_until=task.featured_until,
            )
            self._session.add(model)
        else:
            model.hiver_id = task.hiver_id
            model.status = task.status.value
            model.image_urls = list(task.image_urls)
            model.featured_until = task.featured_until
            model.updated_at = task.updated_at
        await self._session.flush()
        return task

    async def update_status(self, task_id: str, status: str) -> None:
        model = await self._session.get(TaskModel, task_id)
        if model:
            model.status = status

    async def delete(self, task_id: str) -> None:
        model = await self._session.get(TaskModel, task_id)
        if model:
            await self._session.delete(model)
