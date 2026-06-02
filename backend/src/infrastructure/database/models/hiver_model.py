from __future__ import annotations
from sqlalchemy import String, Integer, Boolean, DECIMAL, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geography
from .base import Base


class HiverModel(Base):
    __tablename__ = "hivers"

    user_id:          Mapped[str]  = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    bio:              Mapped[str]  = mapped_column(Text, default="")
    xp_points:        Mapped[int]  = mapped_column(Integer, default=0)
    level:            Mapped[str]  = mapped_column(String(20), default="beginner")
    avg_rating:       Mapped[float]= mapped_column(DECIMAL(3, 2), default=0.0)
    completed_tasks:  Mapped[int]  = mapped_column(Integer, default=0)
    review_count:     Mapped[int]  = mapped_column(Integer, default=0)
    is_available_now: Mapped[bool] = mapped_column(Boolean, default=False)
    work_radius_km:   Mapped[int]  = mapped_column(Integer, default=5)
    location_point:   Mapped[object|None] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    stripe_account_id: Mapped[str|None]   = mapped_column(String(100))

    user:   Mapped["UserModel"]          = relationship("UserModel", back_populates="hiver")
    # selectin: the hiver→domain mapping always reads .skills; async SQLAlchemy
    # can't lazy-load mid-mapping (MissingGreenlet), so eager-load it.
    skills: Mapped[list["SkillModel"]]   = relationship("SkillModel", secondary="hiver_skills", back_populates="hivers", lazy="selectin")
    offers: Mapped[list["OfferModel"]]   = relationship("OfferModel", back_populates="hiver")
    tasks_assigned: Mapped[list["TaskModel"]] = relationship("TaskModel", back_populates="hiver", foreign_keys="TaskModel.hiver_id")
    boosts: Mapped[list["BoostModel"]]   = relationship("BoostModel", back_populates="hiver")
