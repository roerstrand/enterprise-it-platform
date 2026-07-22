from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from data.models.user_model import Base

class ConfigurationItemModel(Base):
    __tablename__ = "configuration_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    ci_type: Mapped[str]
    environment: Mapped[str]
    owner_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))

