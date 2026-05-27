from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


class UserModel(Base):
    __tablename__ = "users"

    id:            Mapped[str]      = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email:         Mapped[str]      = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str]      = mapped_column(String(255), nullable=False)
    full_name:     Mapped[str]      = mapped_column(String(100), nullable=False)
    phone:         Mapped[str|None] = mapped_column(String(20))
    avatar_url:    Mapped[str|None] = mapped_column(String(500))
    role:          Mapped[str]      = mapped_column(String(10), nullable=False)  # 'client' | 'hiver'
    is_active:     Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:    Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client:  Mapped["ClientModel|None"]           = relationship("ClientModel", back_populates="user", uselist=False)
    hiver:   Mapped["HiverModel|None"]            = relationship("HiverModel", back_populates="user", uselist=False)
    reviews_given:    Mapped[list["ReviewModel"]] = relationship("ReviewModel", foreign_keys="ReviewModel.reviewer_id", back_populates="reviewer")
    reviews_received: Mapped[list["ReviewModel"]] = relationship("ReviewModel", foreign_keys="ReviewModel.reviewee_id", back_populates="reviewee")
    messages_sent:    Mapped[list["MessageModel"]]= relationship("MessageModel", back_populates="sender")
    notifications:    Mapped[list["NotificationLogModel"]] = relationship("NotificationLogModel", back_populates="user")
