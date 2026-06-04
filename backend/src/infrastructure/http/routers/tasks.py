from fastapi import APIRouter, File, Query, UploadFile

from src.application.dtos.review_dtos import ReviewResponse, SubmitReviewRequest
from src.application.dtos.task_dtos import (
    BoostTaskResponse,
    CreateTaskRequest,
    TaskDetailResponse,
    TaskSummaryResponse,
)
from src.application.use_cases.reviews.list_reviews_use_case import (
    ListTaskReviewsUseCase,
)
from src.application.use_cases.reviews.submit_review_use_case import (
    SubmitReviewUseCase,
)
from src.application.use_cases.tasks.boost_task_use_case import BoostTaskUseCase
from src.application.use_cases.tasks.complete_task_use_case import (
    CancelTaskUseCase,
    CompleteTaskUseCase,
)
from src.application.use_cases.tasks.create_task_use_case import CreateTaskUseCase
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.application.use_cases.tasks.list_tasks_use_case import ListClientTasksUseCase
from src.application.use_cases.tasks.search_tasks_use_case import SearchTasksUseCase
from src.application.use_cases.tasks.start_task_use_case import StartTaskUseCase
from src.application.use_cases.tasks.upload_task_image_use_case import (
    UploadTaskImageUseCase,
)
from src.domain.errors.domain_errors import StorageNotConfiguredError
from src.domain.interfaces.repositories import PaginatedResult
from src.infrastructure.database.repositories.review_repository import (
    PostgresReviewRepository,
)
from src.infrastructure.database.repositories.task_repository import (
    PostgresTaskRepository,
)
from src.infrastructure.database.repositories.transaction_repository import (
    PostgresTransactionRepository,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
)
from src.infrastructure.http.dependencies import (
    ClientDep,
    EventBusDep,
    HiverDep,
    SessionDep,
    UserPayloadDep,
)
from src.infrastructure.payments.payment_factory import get_payment_port
from src.infrastructure.storage.storage_factory import get_storage_port

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/search", response_model=PaginatedResult[TaskSummaryResponse])
async def search_tasks(
    session: SessionDep,
    vertical: str | None = Query(None, description="home|learn|tech|care|move|events"),
    status: str | None = Query(
        None, description="open|accepted|in_progress|completed|cancelled|disputed"
    ),
    is_urgent: bool | None = Query(None),
    min_budget: float | None = Query(None, ge=0.0),
    max_budget: float | None = Query(None, ge=0.0),
    q: str | None = Query(None, description="Free-text over title/description/subcategory"),
    lat: float | None = Query(None, ge=-90.0, le=90.0),
    lng: float | None = Query(None, ge=-180.0, le=180.0),
    radius_km: float | None = Query(None, gt=0.0, le=100.0),
    sort: str | None = Query(None, description="recent|distance|budget (default recent)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedResult[TaskSummaryResponse]:
    use_case = SearchTasksUseCase(task_repo=PostgresTaskRepository(session))
    return await use_case.execute(
        vertical=vertical,
        status=status,
        is_urgent=is_urgent,
        min_budget=min_budget,
        max_budget=max_budget,
        q=q,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TaskDetailResponse, status_code=201)
async def create_task(
    body: CreateTaskRequest,
    session: SessionDep,
    client: ClientDep,
) -> TaskDetailResponse:
    use_case = CreateTaskUseCase(
        task_repo=PostgresTaskRepository(session),
        client_repo=PostgresClientRepository(session),
    )
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
    bus: EventBusDep,
) -> TaskDetailResponse:
    use_case = StartTaskUseCase(
        task_repo=PostgresTaskRepository(session), event_bus=bus
    )
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
    bus: EventBusDep,
) -> TaskDetailResponse:
    use_case = CancelTaskUseCase(
        task_repo=PostgresTaskRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
        payment_port=get_payment_port(),
        event_bus=bus,
    )
    return await use_case.execute(task_id=task_id, actor_id=client.id)


@router.post("/{task_id}/boost", response_model=BoostTaskResponse)
async def boost_task(
    task_id: str,
    session: SessionDep,
    client: ClientDep,
) -> BoostTaskResponse:
    """Owner pays to feature their task atop search for a week (mock-charged)."""
    use_case = BoostTaskUseCase(
        task_repo=PostgresTaskRepository(session),
        payment_port=get_payment_port(),
    )
    return await use_case.execute(task_id=task_id, client_id=client.id)


@router.post("/{task_id}/images", response_model=TaskDetailResponse)
async def upload_task_image(
    task_id: str,
    session: SessionDep,
    client: ClientDep,
    file: UploadFile = File(...),
) -> TaskDetailResponse:
    storage = get_storage_port()
    if storage is None:
        raise StorageNotConfiguredError()
    data = await file.read()
    use_case = UploadTaskImageUseCase(
        task_repo=PostgresTaskRepository(session),
        storage_port=storage,
    )
    return await use_case.execute(
        task_id=task_id,
        client_id=client.id,
        data=data,
        content_type=file.content_type or "",
    )


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
        task_id=task_id,
        reviewer_id=payload["sub"],
        body=body,
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
