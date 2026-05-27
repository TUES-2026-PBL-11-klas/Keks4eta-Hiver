from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DECIMAL, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class ReviewModel(Base):
    __tablename__ = "reviews"

    id:          Mapped[str]   = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id:     Mapped[str]   = mapped_column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id: Mapped[str]   = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    reviewee_id: Mapped[str]   = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    rating:      Mapped[float] = mapped_column(DECIMAL(3, 2), nullable=False)
    comment:     Mapped[str]   = mapped_column(Text, nullable=False)
    is_revealed: Mapped[bool]  = mapped_column(Boolean, default=False)
    created_at:  Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    task:     Mapped["TaskModel"] = relationship("TaskModel", back_populates="reviews")
    reviewer: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[reviewee_id], back_populates="reviews_received")
