from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DECIMAL, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class OfferModel(Base):
    __tablename__ = "offers"

    id:              Mapped[str]   = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id:         Mapped[str]   = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    hiver_id:        Mapped[str]   = mapped_column(String(36), ForeignKey("hivers.user_id"), nullable=False, index=True)
    price:           Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    message:         Mapped[str]   = mapped_column(Text, nullable=False)
    estimated_hours: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=False)
    status:          Mapped[str]   = mapped_column(String(20), default="pending", index=True)
    created_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    task:  Mapped[TaskModel]  = relationship("TaskModel", back_populates="offers")
    hiver: Mapped[HiverModel] = relationship("HiverModel", back_populates="offers")
