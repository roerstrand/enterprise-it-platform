from sqlalchemy.orm import Mapped, mapped_column

from data.models.user_model import Base

class TeamModel(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
