from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, func, text

from data.models.user_model import Base

class IncidentModel(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    status: Mapped[str] = mapped_column(default="open")
    severity: Mapped[str]
    ci_id: Mapped[int]
    ai_summary: Mapped[str | None] = mapped_column(default=None)
    ai_summary_status: Mapped[str] = mapped_column(server_default=text("'pending'"))
    ai_suggested_severity: Mapped[str | None] = mapped_column(default=None)
    ai_suggested_status: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # onupdate = SQLAlchemy sätter denna själv vid varje UPDATE, ingen manuell "touch" behövs i repository-koden
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

