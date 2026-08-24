from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, ForeignKey, func, text

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
    assignee_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None)
    # Sätts en gång, första gången statusen når in_progress/resolved - se update_incident_status_in_db.
    # SLA-brott beräknas alltid dynamiskt vid läsning (domain/sla.py), dessa två är bara de råa
    # tidsstämplarna beräkningen bygger på.
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    # Dedupe-flaggor för SLA-bevakningsloopen (_sla_watch_loop) - monotona, återställs aldrig,
    # så samma incident larmar bara en gång per gräns den passerar.
    sla_approaching_notified: Mapped[bool] = mapped_column(default=False)
    sla_breached_notified: Mapped[bool] = mapped_column(default=False)

