from sqlalchemy import select
from sqlalchemy.orm import Session

from data.models.incident_model import IncidentModel

def create_incident_in_db(db: Session, title: str, description: str, severity: str, ci_id: int):
    incident = IncidentModel(title=title, description=description, severity=severity, ci_id=ci_id)
    db.add(incident)
    db.commit()
    return incident

def get_incident_by_id_from_db(db: Session, incident_id: int):
    return db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    ).scalars().first()

def get_all_incidents_from_db(db: Session):
    return db.execute(select(IncidentModel)).scalars().all()

