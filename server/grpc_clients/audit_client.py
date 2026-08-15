import os
import json
import grpc
from protos import audit_pb2
from protos import audit_pb2_grpc

AUDIT_SERVICE_ADDR = os.getenv("AUDIT_SERVICE_ADDR", "localhost:50055")

_stub = None

def _get_stub():
    global _stub
    if _stub is None:
        channel = grpc.aio.insecure_channel(AUDIT_SERVICE_ADDR)
        _stub = audit_pb2_grpc.AuditServiceStub(channel)
    return _stub

class AuditServiceUnavailable(Exception):
    pass

def _to_dict(event):
    return {
        "id": event.id,
        "timestamp": event.timestamp,
        "actor_user_id": event.actor_user_id or None,
        "actor_email": event.actor_email or None,
        "action": event.action,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "before": json.loads(event.before_json) if event.before_json else None,
        "after": json.loads(event.after_json) if event.after_json else None,
    }

async def record_audit_event(
    actor_user_id: int | None,
    actor_email: str | None,
    action: str,
    entity_type: str,
    entity_id,
    before: dict | None = None,
    after: dict | None = None,
):
    # Best-effort: revisionsloggning ska aldrig kunna få en business-mutation att misslyckas
    # om audit-servicen är nere. Fel loggas bara till stdout, precis som AI-anropen i incident_server.
    try:
        await _get_stub().RecordAuditEvent(audit_pb2.RecordAuditEventRequest(
            actor_user_id=actor_user_id or 0,
            actor_email=actor_email or "",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            before_json=json.dumps(before) if before is not None else "",
            after_json=json.dumps(after) if after is not None else "",
        ))
    except grpc.RpcError as e:
        print(f"[audit_client] failed to record audit event ({action} {entity_type}#{entity_id}): {e.code()} {e.details()}")

async def list_audit_events(entity_type: str | None = None, entity_id: str | None = None, action: str | None = None, limit: int = 200):
    try:
        response = await _get_stub().ListAuditEvents(audit_pb2.ListAuditEventsRequest(
            entity_type=entity_type or "",
            entity_id=entity_id or "",
            action=action or "",
            limit=limit,
        ))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise AuditServiceUnavailable(str(e))
    return [_to_dict(e) for e in response.events]
