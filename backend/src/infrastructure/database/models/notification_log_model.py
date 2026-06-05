from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .user_model import UserModel

from .base import Base


class NotificationLogModel(Base):
    __tablename__ = "notification_log"

    id:         Mapped[str]  = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id:    Mapped[str]  = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title:      Mapped[str]  = mapped_column(String(200), nullable=False)
    body:       Mapped[str]  = mapped_column(Text, nullable=False)
    data:       Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=dict)
    is_read:    Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    user: Mapped[UserModel] = relationship("UserModel", back_populates="notifications")
