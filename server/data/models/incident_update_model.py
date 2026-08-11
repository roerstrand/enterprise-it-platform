from sqlalchemy.orm import Mapped, mapped_column

from data.models.user_model import Base

class IncidentUpdateModel(Base):
    __tablename__ = "incident_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int]
    text: Mapped[str]

