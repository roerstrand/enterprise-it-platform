from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from data.models.ci_model import ConfigurationItemModel
from data.models.relationship_model import CIRelationshipModel

def create_ci_in_db(db: Session, name: str, ci_type: str, environment: str, owner_team_id: int | None = None):
    ci = ConfigurationItemModel(name=name, ci_type=ci_type, environment=environment, owner_team_id=owner_team_id)
    db.add(ci)
    db.commit()
    return ci

def get_ci_by_id_from_db(db: Session, ci_id: int):
    return db.execute(
        select(ConfigurationItemModel).where(ConfigurationItemModel.id == ci_id)
    ).scalars().first()

def get_all_cis_from_db(db: Session):
    return db.execute(select(ConfigurationItemModel)).scalars().all()

def create_relationship_in_db(db: Session, source_ci_id: int, target_ci_id: int, relationship_type: str):
    relationship = CIRelationshipModel(
        source_ci_id=source_ci_id,
        target_ci_id=target_ci_id,
        relationship_type=relationship_type,
    )
    db.add(relationship)
    db.commit()
    return relationship

def get_related_cis_from_db(db: Session, ci_id: int):
    relationships = db.execute(
        select(CIRelationshipModel).where(
            or_(
                CIRelationshipModel.source_ci_id == ci_id,
                CIRelationshipModel.target_ci_id == ci_id,
            )
        )
    ).scalars().all()

    related_ids = {
        r.target_ci_id if r.source_ci_id == ci_id else r.source_ci_id
        for r in relationships
    }
    if not related_ids:
        return [

        ]
    return db.execute(
        select(ConfigurationItemModel).where(ConfigurationItemModel.id.in_(related_ids))
    ).scalars().all()

