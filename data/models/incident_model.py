from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import text

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

