"""Unit tests for task use cases with in-memory fakes."""
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://t:t@localhost/t")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

import pytest

from src.application.dtos.task_dtos import CreateTaskRequest
from src.application.use_cases.tasks.complete_task_use_case import (
    CancelTaskUseCase,
    CompleteTaskUseCase,
)
from src.application.use_cases.tasks.create_task_use_case import CreateTaskUseCase
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.application.use_cases.tasks.list_tasks_use_case import ListClientTasksUseCase
from src.application.use_cases.tasks.start_task_use_case import StartTaskUseCase
from src.domain.entities.task import Task, TaskStatus
from src.domain.entities.user import Client
from src.domain.errors.domain_errors import ClientNotFoundError, TaskNotFoundError
from src.domain.interfaces.repositories import PaginatedResult
from src.domain.value_objects.rating import Rating


def make_client(cid: str = "c-1") -> Client:
    return Client(id=cid, email=f"{cid}@x.com", _password_hash=None, full_name="User",
                  rating_as_client=Rating(5.0))


def make_task(tid: str = "t-1", client_id: str = "c-1", vertical: str = "home") -> Task:
    return Task(
        id=tid,
        client_id=client_id,
        vertical=vertical,
        subcategory="cleaning",
        title="Clean house",
        description="Need it cleaned",
    )


class FakeClientRepo:
    def __init__(self, clients: list | None = None) -> None:
        self.saved: list = clients or []

    async def find_by_id(self, cid: str):
        return next((c for c in self.saved if c.id == cid), None)

    async def save(self, entity):
        for i, c in enumerate(self.saved):
            if c.id == entity.id:
                self.saved[i] = entity
                return entity
        self.saved.append(entity)
        return entity


class FakeTaskRepo:
    def __init__(self, tasks: list | None = None) -> None:
        self.saved: list = tasks or []

    async def find_by_id(self, tid: str):
        return next((t for t in self.saved if t.id == tid), None)

    async def save(self, task):
        for i, t in enumerate(self.saved):
            if t.id == task.id:
                self.saved[i] = task
                return task
        self.saved.append(task)
        return task

    async def find_by_client(self, client_id: str, page: int = 1, page_size: int = 20):
        items = [t for t in self.saved if t.client_id == client_id]
        return PaginatedResult(items=items, total=len(items), page=page, page_size=page_size)

    async def find_nearby(self, location, radius_km, vertical=None):
        return []

    async def search(self, **kwargs):
        return PaginatedResult(items=list(self.saved), total=len(self.saved), page=1, page_size=20)

    async def update_status(self, task_id: str, status: str) -> None:
        pass

    async def delete(self, task_id: str) -> None:
        self.saved = [t for t in self.saved if t.id != task_id]


class TestCreateTaskUseCase:
    async def test_creates_task_and_returns_response(self):
        client = make_client()
        task_repo = FakeTaskRepo()
        client_repo = FakeClientRepo([client])

        req = CreateTaskRequest(
            vertical="home", subcategory="cleaning",
            title="Clean house", description="Need cleaning",
        )
        resp = await CreateTaskUseCase(task_repo, client_repo).execute(req, "c-1")

        assert resp.vertical == "home"
        assert len(task_repo.saved) == 1
        assert client.total_tasks == 1

    async def test_client_not_found_raises(self):
        with pytest.raises(ClientNotFoundError):
            await CreateTaskUseCase(FakeTaskRepo(), FakeClientRepo()).execute(
                CreateTaskRequest(vertical="home", subcategory="x", title="T", description="D"),
                "missing",
            )

    async def test_invalid_vertical_raises(self):
        client = make_client()
        with pytest.raises(Exception):
            await CreateTaskUseCase(FakeTaskRepo(), FakeClientRepo([client])).execute(
                CreateTaskRequest(vertical="invalid", subcategory="x", title="T", description="D"),
                "c-1",
            )


class TestGetTaskUseCase:
    async def test_returns_task_detail(self):
        task = make_task()
        resp = await GetTaskUseCase(FakeTaskRepo([task])).execute("t-1")
        assert resp.id == "t-1"
        assert resp.vertical == "home"

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await GetTaskUseCase(FakeTaskRepo()).execute("missing")


class TestCompleteTaskUseCase:
    async def test_completes_in_progress_task(self):
        task = make_task()
        task.accept("h-1")
        task.start("h-1")
        assert task.status == TaskStatus.IN_PROGRESS

        task_repo = FakeTaskRepo([task])
        await CompleteTaskUseCase(task_repo).execute("t-1", "c-1")
        assert task.status == TaskStatus.COMPLETED

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await CompleteTaskUseCase(FakeTaskRepo()).execute("nope", "c-1")


class TestCancelTaskUseCase:
    async def test_cancels_open_task(self):
        task = make_task()
        task_repo = FakeTaskRepo([task])
        await CancelTaskUseCase(task_repo).execute("t-1", "c-1")
        assert task.status == TaskStatus.CANCELLED

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await CancelTaskUseCase(FakeTaskRepo()).execute("nope", "c-1")


class TestStartTaskUseCase:
    async def test_starts_accepted_task(self):
        task = make_task()
        task.accept("h-1")
        task_repo = FakeTaskRepo([task])
        resp = await StartTaskUseCase(task_repo).execute("t-1", "h-1")
        assert resp.status == "in_progress"

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await StartTaskUseCase(FakeTaskRepo()).execute("nope", "h-1")


class TestListClientTasksUseCase:
    async def test_returns_paginated_tasks(self):
        tasks = [make_task(f"t-{i}") for i in range(3)]
        task_repo = FakeTaskRepo(tasks)
        result = await ListClientTasksUseCase(task_repo).execute("c-1")
        assert result.total == 3
        assert len(result.items) == 3
