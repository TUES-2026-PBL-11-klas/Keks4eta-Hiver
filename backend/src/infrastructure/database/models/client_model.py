from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import DECIMAL, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .task_model import TaskModel
    from .user_model import UserModel


class ClientModel(Base):
    __tablename__ = "clients"

    user_id:          Mapped[str]   = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    rating_as_client: Mapped[float] = mapped_column(DECIMAL(3, 2), default=5.0)
    total_tasks:      Mapped[int]   = mapped_column(Integer, default=0)
    review_count:     Mapped[int]   = mapped_column(Integer, default=0)
    stripe_customer_id: Mapped[str|None] = mapped_column(String(100))

    user:  Mapped[UserModel]       = relationship("UserModel", back_populates="client")
    tasks: Mapped[list[TaskModel]] = relationship("TaskModel", back_populates="client", foreign_keys="TaskModel.client_id")
