class AppError(Exception):
    """
    Base error class — all application errors inherit from this.
    OOP: Abstraction — callers catch AppError without knowing specifics.
    is_operational=True means expected error (4xx), not a programming bug.
    """

    def __init__(self, message: str, code: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.is_operational = True


# ── Not Found ──────────────────────────────────────────────────────────────


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            code="NOT_FOUND",
            status_code=404,
        )


class TaskNotFoundError(NotFoundError):
    def __init__(self, task_id: str):
        super().__init__("Task", task_id)


class HiverNotFoundError(NotFoundError):
    def __init__(self, hiver_id: str):
        super().__init__("Hiver", hiver_id)


class ClientNotFoundError(NotFoundError):
    def __init__(self, client_id: str):
        super().__init__("Client", client_id)


class OfferNotFoundError(NotFoundError):
    def __init__(self, offer_id: str):
        super().__init__("Offer", offer_id)


class ReviewNotFoundError(NotFoundError):
    def __init__(self, review_id: str):
        super().__init__("Review", review_id)


class DisputeNotFoundError(NotFoundError):
    def __init__(self, task_id: str):
        super().__init__("Dispute for task", task_id)


class TransactionNotFoundError(NotFoundError):
    def __init__(self, transaction_id: str):
        super().__init__("Transaction", transaction_id)


# ── Business Rule Violations (422) ─────────────────────────────────────────


class BusinessRuleViolationError(AppError):
    """Base for all domain rule violations."""

    def __init__(self, message: str, code: str):
        super().__init__(message, code, status_code=422)


class EscrowAlreadyReleasedError(BusinessRuleViolationError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Escrow for task {task_id} has already been released",
            "ESCROW_ALREADY_RELEASED",
        )


class HiverUnavailableError(BusinessRuleViolationError):
    def __init__(self, hiver_id: str):
        super().__init__(
            f"Hiver {hiver_id} is not available for direct booking",
            "HIVER_UNAVAILABLE",
        )


class InsufficientRatingError(BusinessRuleViolationError):
    def __init__(self, client_rating: float):
        super().__init__(
            f"Client rating {client_rating} is too low to post tasks (minimum 2.0)",
            "INSUFFICIENT_CLIENT_RATING",
        )


class TaskAlreadyAcceptedError(BusinessRuleViolationError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Task {task_id} has already been accepted by a hiver",
            "TASK_ALREADY_ACCEPTED",
        )


class OfferAlreadyExistsError(BusinessRuleViolationError):
    def __init__(self, hiver_id: str, task_id: str):
        super().__init__(
            f"Hiver {hiver_id} already submitted an offer for task {task_id}",
            "OFFER_ALREADY_EXISTS",
        )


class CannotOfferOnOwnTaskError(BusinessRuleViolationError):
    """Unified accounts can both post and work — but not offer on themselves."""

    def __init__(self, task_id: str):
        super().__init__(
            f"You cannot make an offer on your own task {task_id}",
            "CANNOT_OFFER_ON_OWN_TASK",
        )


class ReviewAlreadySubmittedError(BusinessRuleViolationError):
    def __init__(self, reviewer_id: str, task_id: str):
        super().__init__(
            f"User {reviewer_id} already submitted a review for task {task_id}",
            "REVIEW_ALREADY_SUBMITTED",
        )


class TaskNotCompletedError(BusinessRuleViolationError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Task {task_id} must be completed before releasing escrow",
            "TASK_NOT_COMPLETED",
        )


class InvalidOfferPriceError(BusinessRuleViolationError):
    def __init__(self, price: object, budget_min: object, budget_max: object):
        super().__init__(
            f"Offer price {price} is outside task budget range {budget_min}–{budget_max}",
            "INVALID_OFFER_PRICE",
        )


class MissingSmartAnswerError(BusinessRuleViolationError):
    """A vertical-specific required answer was not supplied for a task."""

    def __init__(self, vertical: str, field: str):
        super().__init__(
            f"{vertical.capitalize()} tasks require '{field}'",
            "MISSING_SMART_ANSWER",
        )


class InvalidBudgetRangeError(BusinessRuleViolationError):
    """The minimum budget exceeds the maximum budget."""

    def __init__(self, budget_min: object, budget_max: object):
        super().__init__(
            f"Minimum budget {budget_min} cannot exceed maximum budget {budget_max}",
            "INVALID_BUDGET_RANGE",
        )


class DisputeAlreadyExistsError(BusinessRuleViolationError):
    def __init__(self, task_id: str):
        super().__init__(
            f"A dispute has already been opened for task {task_id}",
            "DISPUTE_ALREADY_EXISTS",
        )


class DisputeAlreadyResolvedError(BusinessRuleViolationError):
    def __init__(self, task_id: str):
        super().__init__(
            f"The dispute for task {task_id} is already resolved",
            "DISPUTE_ALREADY_RESOLVED",
        )


class NoEscrowToDisputeError(BusinessRuleViolationError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Task {task_id} has no held escrow to dispute",
            "NO_ESCROW_TO_DISPUTE",
        )


# ── Auth / Authorization ───────────────────────────────────────────────────


class UnauthorizedActionError(AppError):
    def __init__(self, action: str):
        super().__init__(
            f"You are not authorized to {action}",
            "UNAUTHORIZED",
            status_code=403,
        )


class InvalidCredentialsError(AppError):
    def __init__(self) -> None:
        super().__init__("Invalid email or password", "INVALID_CREDENTIALS", 401)


class TokenExpiredError(AppError):
    def __init__(self) -> None:
        super().__init__("Token has expired", "TOKEN_EXPIRED", 401)


class InvalidTokenError(AppError):
    def __init__(self) -> None:
        super().__init__("Token is invalid", "INVALID_TOKEN", 401)


class OAuthProviderNotConfiguredError(AppError):
    def __init__(self, provider: str) -> None:
        super().__init__(
            f"Social login provider '{provider}' is not configured on this server",
            "OAUTH_NOT_CONFIGURED",
            503,
        )


class OAuthError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(f"Social login failed: {detail}", "OAUTH_FAILED", 401)


# ── Service availability ───────────────────────────────────────────────────


class StorageNotConfiguredError(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Image uploads are not configured on this server",
            "STORAGE_NOT_CONFIGURED",
            503,
        )


# ── Validation ─────────────────────────────────────────────────────────────


class InvalidEmailError(AppError):
    def __init__(self, email: str):
        super().__init__(f"Invalid email address: {email}", "INVALID_EMAIL", 400)


class DuplicateEmailError(AppError):
    def __init__(self, email: str):
        super().__init__(
            f"An account with email {email} already exists",
            "DUPLICATE_EMAIL",
            409,
        )


class InvalidVerticalError(AppError):
    def __init__(self, vertical: str):
        super().__init__(f"Unknown task vertical: {vertical}", "INVALID_VERTICAL", 400)
