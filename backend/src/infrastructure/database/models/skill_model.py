from __future__ import annotations

import uuid

from sqlalchemy import Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

hiver_skills = Table(
    "hiver_skills",
    Base.metadata,
    Column("hiver_id", String(36), ForeignKey("hivers.user_id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", String(36), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class SkillModel(Base):
    __tablename__ = "skills"

    id:       Mapped[str]      = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name:     Mapped[str]      = mapped_column(String(80), unique=True, nullable=False)
    vertical: Mapped[str|None] = mapped_column(String(20))

    hivers: Mapped[list[HiverModel]] = relationship("HiverModel", secondary="hiver_skills", back_populates="skills")
