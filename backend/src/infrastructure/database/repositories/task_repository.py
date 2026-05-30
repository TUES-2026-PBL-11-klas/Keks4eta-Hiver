from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.domain.entities.task import Task, TaskStatus
from src.domain.value_objects.money import Money
from src.domain.value_objects.location import Location
from src.domain.interfaces.repositories import ITaskRepository, PaginatedResult
from src.infrastructure.database.models import TaskModel


def _model_to_domain(m: TaskModel) -> Task:
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
        location=Location(0, 0, m.location_display) if m.location_display else None,
        smart_answers=m.smart_answers or {},
        image_urls=m.image_urls or [],
        expires_at=m.expires_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class PostgresTaskRepository(ITaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, task_id: str) -> Task | None:
        model = await self._session.get(TaskModel, task_id)
        return _model_to_domain(model) if model else None

    async def find_nearby(self, location: Location, radius_km: int, vertical: str | None = None) -> list[Task]:
        from sqlalchemy import text
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
        result = await self._session.execute(query, {
            "lat": location.latitude, "lng": location.longitude,
            "radius_m": radius_km * 1000, "vertical": vertical,
        })
        ids = [row.id for row in result]
        tasks = []
        for task_id in ids:
            model = await self._session.get(TaskModel, task_id)
            if model:
                tasks.append(_model_to_domain(model))
        return tasks

    async def search(
        self,
        vertical: str | None = None,
        status: str | None = None,
        is_urgent: bool | None = None,
        min_budget: float | None = None,
        max_budget: float | None = None,
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

        count_q = select(func.count()).select_from(TaskModel)
        list_q = select(TaskModel).order_by(TaskModel.created_at.desc())
        for f in filters:
            count_q = count_q.where(f)
            list_q = list_q.where(f)

        total = (await self._session.execute(count_q)).scalar_one()
        result = await self._session.execute(
            list_q.offset((page - 1) * page_size).limit(page_size)
        )
        items = [_model_to_domain(m) for m in result.scalars()]
        return PaginatedResult(items=items, total=total, page=page, page_size=page_size)

    async def find_by_client(self, client_id: str, page: int = 1, page_size: int = 20) -> PaginatedResult[Task]:
        count_result = await self._session.execute(
            select(func.count()).select_from(TaskModel).where(TaskModel.client_id == client_id)
        )
        total = count_result.scalar_one()

        result = await self._session.execute(
            select(TaskModel)
            .where(TaskModel.client_id == client_id)
            .order_by(TaskModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [_model_to_domain(m) for m in result.scalars()]
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
                location_display=task.location.display_address if task.location else None,
                smart_answers=task.smart_answers,
                image_urls=task.image_urls,
                expires_at=task.expires_at,
            )
            self._session.add(model)
        else:
            model.hiver_id = task.hiver_id
            model.status = task.status.value
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
