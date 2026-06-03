from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TransactionModel(Base):
    __tablename__ = "transactions"

    id:                       Mapped[str]         = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id:                  Mapped[str]         = mapped_column(String(36), ForeignKey("tasks.id"), unique=True, nullable=False)
    client_id:                Mapped[str]         = mapped_column(String(36), ForeignKey("clients.user_id"), nullable=False)
    hiver_id:                 Mapped[str]         = mapped_column(String(36), ForeignKey("hivers.user_id"), nullable=False)
    gross_amount:             Mapped[float]       = mapped_column(DECIMAL(10, 2), nullable=False)
    platform_fee:             Mapped[float]       = mapped_column(DECIMAL(10, 2), nullable=False)
    hiver_payout:             Mapped[float]       = mapped_column(DECIMAL(10, 2), nullable=False)
    stripe_payment_intent_id: Mapped[str]         = mapped_column(String(200), nullable=False)
    status:                   Mapped[str]         = mapped_column(String(20), default="held", index=True)
    released_at:              Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    refunded_at:              Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    created_at:               Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:               Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    task: Mapped[TaskModel] = relationship("TaskModel", back_populates="transaction")
