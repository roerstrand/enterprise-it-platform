import os
import grpc
from protos import incident_pb2
from protos import incident_pb2_grpc

INCIDENT_SERVICE_ADDR = os.getenv("INCIDENT_SERVICE_ADDR", "localhost:50053")

_stub = None

def _get_stub():
    global _stub
    if _stub is None:
        channel = grpc.aio.insecure_channel(INCIDENT_SERVICE_ADDR)
        _stub = incident_pb2_grpc.IncidentServiceStub(channel)
    return _stub

class IncidentServiceUnavailable(Exception):
    pass

class IncidentNotFound(Exception):
    pass

class InvalidIncidentInput(Exception):
    pass

def _to_dict(incident):
    return {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "status": incident.status,
        "severity": incident.severity,
        "ci_id": incident.ci_id,
        "ai_summary": incident.ai_summary,
        "ai_summary_status": incident.ai_summary_status,
        "ai_suggested_severity": incident.ai_suggested_severity,
        "ai_suggested_status": incident.ai_suggested_status,
        "created_at": incident.created_at,
        "updated_at": incident.updated_at,
        "assignee_user_id": incident.assignee_user_id or None,
        "sla": {
            "response_deadline": incident.sla_response_deadline,
            "resolution_deadline": incident.sla_resolution_deadline,
            "first_response_at": incident.sla_first_response_at or None,
            "resolved_at": incident.sla_resolved_at or None,
            "response_breached": incident.sla_response_breached,
            "resolution_breached": incident.sla_resolution_breached,
            "state": incident.sla_state,
            "remaining_seconds": incident.sla_remaining_seconds,
        },
    }

def _to_update_dict(update):
    return {
        "id": update.id,
        "incident_id": update.incident_id,
        "text": update.text,
        "author_user_id": update.author_user_id or None,
        "created_at": update.created_at,
    }

def _to_with_ci_dict(response):
    return {
        **_to_dict(response.incident),
        "ci_name": response.ci_name,
        "ci_environment": response.ci_environment,
        "ci_type": response.ci_type,
        "owner_name": response.owner_name,
        "owner_email": response.owner_email,
    }

async def _call(coro):
    try:
        return await coro
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise IncidentNotFound(str(e))
        if e.code() in (grpc.StatusCode.INVALID_ARGUMENT, grpc.StatusCode.FAILED_PRECONDITION):
            raise InvalidIncidentInput(e.details())
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise IncidentServiceUnavailable(str(e))

async def list_incidents(
    status: str | None = None,
    severity: str | None = None,
    assignee_user_id: int | None = None,
    unassigned_only: bool = False,
    ci_id: int | None = None,
    sla_state: str | None = None,
    search: str | None = None,
    created_after: str | None = None,
    created_before: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    page: int = 1,
    page_size: int = 25,
):
    response = await _call(_get_stub().ListIncidents(incident_pb2.ListIncidentsRequest(
        status=status or "", severity=severity or "",
        assignee_user_id=assignee_user_id or 0, unassigned_only=unassigned_only,
        ci_id=ci_id or 0, sla_state=sla_state or "", search=search or "",
        created_after=created_after or "", created_before=created_before or "",
        sort_by=sort_by or "created_at", sort_dir=sort_dir or "desc",
        page=page or 1, page_size=page_size or 25,
    )))
    return {
        "incidents": [_to_dict(i) for i in response.incidents],
        "total_count": response.total_count,
        "page": response.page,
        "page_size": response.page_size,
    }

async def assign_incident(incident_id: int, assignee_user_id: int | None, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().AssignIncident(incident_pb2.AssignIncidentRequest(
        id=incident_id, assignee_user_id=assignee_user_id or 0,
        actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def get_incident_with_ci(incident_id: int):
    response = await _call(_get_stub().GetIncidentWithCI(incident_pb2.IncidentIdRequest(id=incident_id)))
    return _to_with_ci_dict(response)

async def get_incident(incident_id: int):
    response = await _call(_get_stub().GetIncident(incident_pb2.IncidentIdRequest(id=incident_id)))
    return _to_dict(response)

async def link_change(incident_id: int, change_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    await _call(_get_stub().LinkChange(incident_pb2.LinkChangeRequest(
        incident_id=incident_id, change_id=change_id, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))

async def unlink_change(incident_id: int, change_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    await _call(_get_stub().UnlinkChange(incident_pb2.LinkChangeRequest(
        incident_id=incident_id, change_id=change_id, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))

async def get_linked_change_ids(incident_id: int) -> list[int]:
    response = await _call(_get_stub().GetLinkedChangeIds(incident_pb2.IncidentIdRequest(id=incident_id)))
    return list(response.change_ids)

async def get_incident_ids_for_change(change_id: int) -> list[int]:
    response = await _call(_get_stub().GetIncidentIdsForChange(incident_pb2.ChangeIdRequest(change_id=change_id)))
    return list(response.incident_ids)

async def create_incident(title: str, description: str, severity: str, ci_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().CreateIncident(incident_pb2.CreateIncidentRequest(
        title=title, description=description, severity=severity, ci_id=ci_id,
        actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def add_incident_update(incident_id: int, text: str, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().AddIncidentUpdate(incident_pb2.AddIncidentUpdateRequest(
        incident_id=incident_id, text=text, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def get_incident_updates(incident_id: int):
    response = await _call(_get_stub().GetIncidentUpdates(incident_pb2.IncidentIdRequest(id=incident_id)))
    return [_to_update_dict(u) for u in response.updates]

async def accept_suggested_severity(incident_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().AcceptSuggestedSeverity(incident_pb2.IncidentActionRequest(
        id=incident_id, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def accept_suggested_status(incident_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().AcceptSuggestedStatus(incident_pb2.IncidentActionRequest(
        id=incident_id, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def update_incident(incident_id: int, title: str, description: str, severity: str, ci_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().UpdateIncident(incident_pb2.UpdateIncidentRequest(
        id=incident_id, title=title, description=description, severity=severity, ci_id=ci_id,
        actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def update_incident_status(incident_id: int, status: str, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().UpdateIncidentStatus(incident_pb2.UpdateIncidentStatusRequest(
        id=incident_id, status=status, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def update_incident_severity(incident_id: int, severity: str, actor_user_id: int | None = None, actor_email: str | None = None):
    response = await _call(_get_stub().UpdateIncidentSeverity(incident_pb2.UpdateIncidentSeverityRequest(
        id=incident_id, severity=severity, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
    return _to_dict(response)

async def delete_incident(incident_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    await _call(_get_stub().DeleteIncident(incident_pb2.IncidentActionRequest(
        id=incident_id, actor_user_id=actor_user_id or 0, actor_email=actor_email or "",
    )))
