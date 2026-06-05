from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geography
from sqlalchemy import ARRAY, DECIMAL, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .client_model import ClientModel
    from .dispute_model import DisputeModel
    from .hiver_model import HiverModel
    from .message_model import MessageModel
    from .offer_model import OfferModel
    from .review_model import ReviewModel
    from .transaction_model import TransactionModel

from .base import Base


class TaskModel(Base):
    __tablename__ = "tasks"

    id:               Mapped[str]         = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id:        Mapped[str]         = mapped_column(String(36), ForeignKey("clients.user_id"), nullable=False, index=True)
    hiver_id:         Mapped[str|None]    = mapped_column(String(36), ForeignKey("hivers.user_id"), index=True)
    vertical:         Mapped[str]         = mapped_column(String(20), nullable=False, index=True)
    subcategory:      Mapped[str]         = mapped_column(String(50), nullable=False)
    title:            Mapped[str]         = mapped_column(String(200), nullable=False)
    description:      Mapped[str]         = mapped_column(Text, nullable=False)
    status:           Mapped[str]         = mapped_column(String(20), default="open", index=True)
    budget_min:       Mapped[float|None]  = mapped_column(DECIMAL(10, 2))
    budget_max:       Mapped[float|None]  = mapped_column(DECIMAL(10, 2))
    is_urgent:        Mapped[bool]        = mapped_column(Boolean, default=False)
    location_point:   Mapped[object|None] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    location_display: Mapped[str|None]    = mapped_column(String(200))
    smart_answers:    Mapped[dict[str, Any] | None] = mapped_column(JSONB, default=dict)
    image_urls:       Mapped[list[str]]   = mapped_column(ARRAY(Text), default=list)
    expires_at:       Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
    featured_until:   Mapped[datetime|None] = mapped_column(DateTime(timezone=True), index=True)
    created_at:       Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:       Mapped[datetime]    = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client:      Mapped[ClientModel]         = relationship("ClientModel", back_populates="tasks", foreign_keys=[client_id])
    hiver:       Mapped[HiverModel|None]     = relationship("HiverModel", back_populates="tasks_assigned", foreign_keys=[hiver_id])
    offers:      Mapped[list[OfferModel]]    = relationship("OfferModel", back_populates="task")
    transaction: Mapped[TransactionModel|None] = relationship("TransactionModel", back_populates="task", uselist=False)
    reviews:     Mapped[list[ReviewModel]]   = relationship("ReviewModel", back_populates="task")
    messages:    Mapped[list[MessageModel]]  = relationship("MessageModel", back_populates="task")
    dispute:     Mapped[DisputeModel|None]   = relationship("DisputeModel", back_populates="task", uselist=False)
