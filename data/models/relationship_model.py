from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from data.models.user_model import Base

class CIRelationshipModel(Base):
    __tablename__ = "ci_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_ci_id: Mapped[int] = mapped_column(ForeignKey("configuration_items.id"))
    target_ci_id: Mapped[int] = mapped_column(ForeignKey("configuration_items.id"))
    relationship_type: Mapped[str]

