from fastapi import APIRouter, Query

from src.infrastructure.http.dependencies import (
    SessionDep, ClientDep, HiverDep, UserPayloadDep,
)
from src.infrastructure.database.repositories.task_repository import PostgresTaskRepository
from src.infrastructure.database.repositories.review_repository import (
    PostgresReviewRepository,
)
from src.application.use_cases.tasks.create_task_use_case import CreateTaskUseCase
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.application.use_cases.tasks.list_tasks_use_case import ListClientTasksUseCase
from src.application.use_cases.tasks.search_tasks_use_case import SearchTasksUseCase
from src.application.use_cases.tasks.start_task_use_case import StartTaskUseCase
from src.application.use_cases.tasks.complete_task_use_case import (
    CompleteTaskUseCase, CancelTaskUseCase,
)
from src.application.use_cases.reviews.submit_review_use_case import (
    SubmitReviewUseCase,
)
from src.application.use_cases.reviews.list_reviews_use_case import (
    ListTaskReviewsUseCase,
)
from src.application.dtos.task_dtos import (
    CreateTaskRequest, TaskDetailResponse, TaskSummaryResponse,
)
from src.application.dtos.review_dtos import SubmitReviewRequest, ReviewResponse
from src.domain.interfaces.repositories import PaginatedResult

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/search", response_model=PaginatedResult[TaskSummaryResponse])
async def search_tasks(
    session: SessionDep,
    vertical: str | None = Query(None, description="home|learn|tech|care|move|events"),
    status: str | None = Query(None, description="open|accepted|in_progress|completed|cancelled|disputed"),
    is_urgent: bool | None = Query(None),
    min_budget: float | None = Query(None, ge=0.0),
    max_budget: float | None = Query(None, ge=0.0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResult[TaskSummaryResponse]:
    use_case = SearchTasksUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(
        vertical=vertical, status=status, is_urgent=is_urgent,
        min_budget=min_budget, max_budget=max_budget,
        page=page, page_size=page_size,
    )


@router.post("", response_model=TaskDetailResponse, status_code=201)
async def create_task(
    body: CreateTaskRequest,
    session: SessionDep,
    client: ClientDep,
) -> TaskDetailResponse:
    use_case = CreateTaskUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(body, client_id=client.id)


@router.get("", response_model=PaginatedResult[TaskSummaryResponse])
async def list_my_tasks(
    session: SessionDep,
    client: ClientDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResult[TaskSummaryResponse]:
    use_case = ListClientTasksUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(client_id=client.id, page=page, page_size=page_size)


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: str,
    session: SessionDep,
) -> TaskDetailResponse:
    use_case = GetTaskUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(task_id)


@router.post("/{task_id}/start", response_model=TaskDetailResponse)
async def start_task(
    task_id: str,
    session: SessionDep,
    hiver: HiverDep,
) -> TaskDetailResponse:
    use_case = StartTaskUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(task_id=task_id, hiver_id=hiver.id)


@router.post("/{task_id}/complete", response_model=TaskDetailResponse)
async def complete_task(
    task_id: str,
    session: SessionDep,
    client: ClientDep,
) -> TaskDetailResponse:
    use_case = CompleteTaskUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(task_id=task_id, client_id=client.id)


@router.post("/{task_id}/cancel", response_model=TaskDetailResponse)
async def cancel_task(
    task_id: str,
    session: SessionDep,
    client: ClientDep,
) -> TaskDetailResponse:
    use_case = CancelTaskUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(task_id=task_id, actor_id=client.id)


@router.post(
    "/{task_id}/reviews",
    response_model=ReviewResponse,
    status_code=201,
)
async def submit_review(
    task_id: str,
    body: SubmitReviewRequest,
    session: SessionDep,
    payload: UserPayloadDep,
) -> ReviewResponse:
    use_case = SubmitReviewUseCase(
        task_repo=PostgresTaskRepository(session),
        review_repo=PostgresReviewRepository(session),
    )
    return await use_case.execute(
        task_id=task_id, reviewer_id=payload["sub"], body=body,
    )


@router.get("/{task_id}/reviews", response_model=list[ReviewResponse])
async def list_task_reviews(
    task_id: str,
    session: SessionDep,
    only_revealed: bool = True,
) -> list[ReviewResponse]:
    use_case = ListTaskReviewsUseCase(
        review_repo=PostgresReviewRepository(session),
    )
    return await use_case.execute(task_id=task_id, only_revealed=only_revealed)
