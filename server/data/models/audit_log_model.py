from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from data.models.user_model import Base

class AuditLogModel(Base):
    # Append-only: ingen repository-funktion i det här projektet gör UPDATE/DELETE mot denna tabell.
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    actor_user_id: Mapped[int | None] = mapped_column(default=None)
    actor_email: Mapped[str | None] = mapped_column(default=None)
    action: Mapped[str]
    entity_type: Mapped[str]
    entity_id: Mapped[str]
    # JSON-strängar (inte JSON-kolumn) - enklast portabelt mellan SQLite (lokal dev) och Postgres
    before_json: Mapped[str | None] = mapped_column(default=None)
    after_json: Mapped[str | None] = mapped_column(default=None)
