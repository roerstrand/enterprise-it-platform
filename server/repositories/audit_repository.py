from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models.audit_log_model import AuditLogModel

async def create_audit_event_in_db(
    db: AsyncSession,
    actor_user_id: int | None,
    actor_email: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    before_json: str | None,
    after_json: str | None,
):
    event = AuditLogModel(
        actor_user_id=actor_user_id,
        actor_email=actor_email,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before_json,
        after_json=after_json,
    )
    db.add(event)
    await db.commit()
    return event

async def list_audit_events_from_db(
    db: AsyncSession,
    entity_type: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    limit: int = 200,
):
    query = select(AuditLogModel)
    if entity_type:
        query = query.where(AuditLogModel.entity_type == entity_type)
    if entity_id:
        query = query.where(AuditLogModel.entity_id == entity_id)
    if action:
        query = query.where(AuditLogModel.action == action)
    query = query.order_by(AuditLogModel.id.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
