from sqlalchemy.orm import Mapped, mapped_column

from data.models.user_model import Base

class IncidentModel(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    status: Mapped[str] = mapped_column(default="open")
    severity: Mapped[str]
    ci_id: Mapped[int]

