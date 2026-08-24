from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.incident_change_link_model import IncidentChangeLinkModel

async def link_change_in_db(db: AsyncSession, incident_id: int, change_id: int, linked_by_user_id: int | None):
    existing = await db.execute(
        select(IncidentChangeLinkModel).where(
            IncidentChangeLinkModel.incident_id == incident_id,
            IncidentChangeLinkModel.change_id == change_id,
        )
    )
    if existing.scalars().first():
        return False
    db.add(IncidentChangeLinkModel(incident_id=incident_id, change_id=change_id, linked_by_user_id=linked_by_user_id))
    await db.commit()
    return True

async def unlink_change_in_db(db: AsyncSession, incident_id: int, change_id: int):
    result = await db.execute(
        select(IncidentChangeLinkModel).where(
            IncidentChangeLinkModel.incident_id == incident_id,
            IncidentChangeLinkModel.change_id == change_id,
        )
    )
    link = result.scalars().first()
    if not link:
        return False
    await db.delete(link)
    await db.commit()
    return True

async def get_change_ids_for_incident(db: AsyncSession, incident_id: int) -> list[int]:
    result = await db.execute(
        select(IncidentChangeLinkModel.change_id).where(IncidentChangeLinkModel.incident_id == incident_id)
    )
    return [row[0] for row in result.all()]

async def get_incident_ids_for_change(db: AsyncSession, change_id: int) -> list[int]:
    result = await db.execute(
        select(IncidentChangeLinkModel.incident_id).where(IncidentChangeLinkModel.change_id == change_id)
    )
    return [row[0] for row in result.all()]
