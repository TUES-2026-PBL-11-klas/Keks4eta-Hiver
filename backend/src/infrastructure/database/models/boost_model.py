from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class BoostModel(Base):
    __tablename__ = "boosts"

    id:                Mapped[str]         = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hiver_id:          Mapped[str]         = mapped_column(String(36), ForeignKey("hivers.user_id", ondelete="CASCADE"), nullable=False, index=True)
    vertical:          Mapped[str|None]    = mapped_column(String(20))
    expires_at:        Mapped[datetime]    = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    stripe_payment_id: Mapped[str]         = mapped_column(String(200), nullable=False)
    created_at:        Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())

    hiver: Mapped["HiverModel"] = relationship("HiverModel", back_populates="boosts")
