from src.application.dtos.task_dtos import (
    TASK_BOOST_DURATION_DAYS,
    TASK_BOOST_PRICE_BGN,
    BoostTaskResponse,
)
from src.domain.errors.domain_errors import (
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.interfaces.ports import IPaymentPort
from src.domain.interfaces.repositories import ITaskRepository
from src.domain.value_objects.money import Money


class BoostTaskUseCase:
    """Task owner pays to promote their task to the top of search for a week.

    Charged through the payment port (mock by default), mirroring the hiver
    visibility boost. Buying again while still featured extends the window.
    """

    def __init__(self, task_repo: ITaskRepository, payment_port: IPaymentPort) -> None:
        self._task_repo = task_repo
        self._payment_port = payment_port

    async def execute(self, task_id: str, client_id: str) -> BoostTaskResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if task.client_id != client_id:
            raise UnauthorizedActionError("boost this task")

        await self._payment_port.hold_payment(Money.of(TASK_BOOST_PRICE_BGN), client_id)
        task.feature(TASK_BOOST_DURATION_DAYS)
        await self._task_repo.save(task)

        assert task.featured_until is not None  # set by feature()
        return BoostTaskResponse(task_id=task.id, featured_until=task.featured_until)
