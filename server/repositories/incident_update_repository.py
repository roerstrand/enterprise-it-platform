from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.incident_update_model import IncidentUpdateModel

async def create_incident_update_in_db(db: AsyncSession, incident_id: int, text: str):
    update = IncidentUpdateModel(incident_id=incident_id, text=text)
    db.add(update)
    await db.commit()
    return update

async def get_updates_for_incident_from_db(db: AsyncSession, incident_id: int):
    result = await db.execute(
        select(IncidentUpdateModel).where(IncidentUpdateModel.incident_id == incident_id).order_by(IncidentUpdateModel.id)
    )
    return result.scalars().all()

