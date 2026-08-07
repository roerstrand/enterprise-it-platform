from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.incident_model import IncidentModel

async def create_incident_in_db(db: AsyncSession, title: str, description: str, severity: str, ci_id: int):
    incident = IncidentModel(title=title, description=description, severity=severity, ci_id=ci_id)
    db.add(incident)
    await db.commit()
    return incident

async def get_incident_by_id_from_db(db: AsyncSession, incident_id: int):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    return result.scalars().first()

async def get_all_incidents_from_db(db: AsyncSession):
    result = await db.execute(select(IncidentModel))
    return result.scalars().all()

async def update_incident_ai_summary(db: AsyncSession, incident_id: int, ai_summary: str):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.ai_summary = ai_summary
        incident.ai_summary_status = "ready"
        await db.commit()

async def mark_incident_ai_summary_failed(db: AsyncSession, incident_id: int):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.ai_summary_status = "failed"
        await db.commit()

async def update_incident_ai_suggested_severity(db: AsyncSession, incident_id: int, suggested_severity: str):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.ai_suggested_severity = suggested_severity
        await db.commit()

async def update_incident_ai_suggested_status(db: AsyncSession, incident_id: int, suggested_status: str):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.ai_suggested_status = suggested_status
        await db.commit()

