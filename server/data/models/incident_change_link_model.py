from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from data.models.user_model import Base

class IncidentChangeLinkModel(Base):
    # Ägs av Incident Service (den tjänst som initierar länken). change_id är avsiktligt bara ett
    # int, ingen FK - Change lever i en annan tjänsts domän (C#/EF Core-migrerad tabell), att lägga
    # en FK-constraint tvärs över den gränsen skulle koppla ihop två oberoende migrationsverktyg.
    __tablename__ = "incident_change_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(ForeignKey("incidents.id"))
    change_id: Mapped[int]
    linked_by_user_id: Mapped[int | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
