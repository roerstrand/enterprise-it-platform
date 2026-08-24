from datetime import datetime, timezone

from sqlalchemy import func, or_, select
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

_SORTABLE_COLUMNS = {
    "created_at": IncidentModel.created_at,
    "updated_at": IncidentModel.updated_at,
    "severity": IncidentModel.severity,
    "status": IncidentModel.status,
}

async def list_incidents_filtered_from_db(
    db: AsyncSession,
    *,
    status: str | None = None,
    severity: str | None = None,
    assignee_user_id: int | None = None,
    unassigned_only: bool = False,
    ci_id: int | None = None,
    search: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    limit: int | None = None,
    offset: int = 0,
):
    query = select(IncidentModel)
    count_query = select(func.count()).select_from(IncidentModel)

    def _apply(q):
        if status:
            q = q.where(IncidentModel.status == status)
        if severity:
            q = q.where(IncidentModel.severity == severity)
        if unassigned_only:
            q = q.where(IncidentModel.assignee_user_id.is_(None))
        elif assignee_user_id is not None:
            q = q.where(IncidentModel.assignee_user_id == assignee_user_id)
        if ci_id is not None:
            q = q.where(IncidentModel.ci_id == ci_id)
        if search:
            term = f"%{search}%"
            q = q.where(or_(IncidentModel.title.ilike(term), IncidentModel.description.ilike(term)))
        if created_after is not None:
            q = q.where(IncidentModel.created_at >= created_after)
        if created_before is not None:
            q = q.where(IncidentModel.created_at <= created_before)
        return q

    query = _apply(query)
    count_query = _apply(count_query)

    column = _SORTABLE_COLUMNS.get(sort_by, IncidentModel.created_at)
    query = query.order_by(column.asc() if sort_dir == "asc" else column.desc())
    if limit is not None:
        query = query.limit(limit).offset(offset)

    total_count = (await db.execute(count_query)).scalar_one()
    incidents = (await db.execute(query)).scalars().all()
    return incidents, total_count

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

async def accept_incident_suggested_severity(db: AsyncSession, incident_id: int):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident and incident.ai_suggested_severity:
        # AI returnerar UPPERCASE (t.ex. "HIGH"); status/severity lagras alltid lowercase i DB
        incident.severity = incident.ai_suggested_severity.lower()
        await db.commit()
        await db.refresh(incident)
    return incident

def _apply_sla_timestamps(incident: IncidentModel, new_status: str) -> None:
    # Sätts bara en gång vardera (first_response_at/resolved_at) - en incident som lämnar och
    # återvänder till en status ska inte flytta fram sina egna SLA-tidsstämplar.
    now = datetime.now(timezone.utc)
    if new_status == "in_progress" and incident.first_response_at is None:
        incident.first_response_at = now
    if new_status == "resolved" and incident.resolved_at is None:
        incident.resolved_at = now

async def accept_incident_suggested_status(db: AsyncSession, incident_id: int):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident and incident.ai_suggested_status:
        new_status = incident.ai_suggested_status.lower()
        incident.status = new_status
        _apply_sla_timestamps(incident, new_status)
        await db.commit()
        await db.refresh(incident)
    return incident

async def update_incident_status_in_db(db: AsyncSession, incident_id: int, status: str):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.status = status
        _apply_sla_timestamps(incident, status)
        await db.commit()
        # updated_at har onupdate=func.now() (server-side) - måste refreshas explicit efter commit,
        # annars ger senare attributläsning (t.ex. i _to_incident_response) MissingGreenlet i async-läge.
        await db.refresh(incident)
    return incident

async def update_incident_assignee_in_db(db: AsyncSession, incident_id: int, assignee_user_id: int | None):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.assignee_user_id = assignee_user_id
        await db.commit()
        await db.refresh(incident)
    return incident

async def update_incident_severity_in_db(db: AsyncSession, incident_id: int, severity: str):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.severity = severity
        await db.commit()
        await db.refresh(incident)
    return incident

async def update_incident_in_db(db: AsyncSession, incident_id: int, title: str, description: str, severity: str, ci_id: int):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if incident:
        incident.title = title
        incident.description = description
        incident.severity = severity
        incident.ci_id = ci_id
        await db.commit()
        await db.refresh(incident)
    return incident

async def delete_incident_from_db(db: AsyncSession, incident_id: int):
    result = await db.execute(
        select(IncidentModel).where(IncidentModel.id == incident_id)
    )
    incident = result.scalars().first()
    if not incident:
        return False
    await db.delete(incident)
    await db.commit()
    return True

