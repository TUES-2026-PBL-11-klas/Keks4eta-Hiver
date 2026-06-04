from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .task_model import TaskModel


class DisputeModel(Base):
    __tablename__ = "disputes"

    id:           Mapped[str]         = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id:      Mapped[str]         = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), unique=True, nullable=False)
    opened_by_id: Mapped[str]         = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    reason:       Mapped[str]         = mapped_column(Text, nullable=False)
    status:       Mapped[str]         = mapped_column(String(20), default="open")  # open | resolved | refunded
    admin_note:   Mapped[str|None]    = mapped_column(Text)
    created_at:   Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at:  Mapped[datetime|None] = mapped_column(DateTime(timezone=True))

    task: Mapped[TaskModel] = relationship("TaskModel", back_populates="dispute")
