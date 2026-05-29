from pydantic import BaseModel, field_validator
from datetime import datetime


class CreateOfferRequest(BaseModel):
    price: float
    message: str
    estimated_hours: float

    @field_validator("price")
    @classmethod
    def price_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("estimated_hours")
    @classmethod
    def hours_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Estimated hours must be greater than 0")
        return v

    @field_validator("message")
    @classmethod
    def message_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class OfferResponse(BaseModel):
    id: str
    task_id: str
    hiver_id: str
    price: float
    message: str
    estimated_hours: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
