from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .task_model import TaskModel
    from .user_model import UserModel


class MessageModel(Base):
    __tablename__ = "messages"

    id:         Mapped[str]  = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id:    Mapped[str]  = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id:  Mapped[str]  = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    content:    Mapped[str]  = mapped_column(Text, nullable=False)
    is_read:    Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    task:   Mapped[TaskModel] = relationship("TaskModel", back_populates="messages")
    sender: Mapped[UserModel] = relationship("UserModel", back_populates="messages_sent")
