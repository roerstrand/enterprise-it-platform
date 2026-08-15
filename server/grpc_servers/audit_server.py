import asyncio
import grpc

from protos import audit_pb2, audit_pb2_grpc

from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from repositories.audit_repository import create_audit_event_in_db, list_audit_events_from_db

from data.database import get_db_context
from prometheus_client import start_http_server
from observability.grpc_metrics import track_grpc_metrics
from observability.tracing import setup_tracing

def _to_event_response(event):
    return audit_pb2.AuditEvent(
        id=event.id,
        timestamp=event.timestamp.isoformat(),
        actor_user_id=event.actor_user_id or 0,
        actor_email=event.actor_email or "",
        action=event.action,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        before_json=event.before_json or "",
        after_json=event.after_json or "",
    )

class AuditServiceServicer(audit_pb2_grpc.AuditServiceServicer):

    @track_grpc_metrics("audit")
    async def RecordAuditEvent(self, request, context):
        async with get_db_context() as db:
            await create_audit_event_in_db(
                db,
                actor_user_id=request.actor_user_id or None,
                actor_email=request.actor_email or None,
                action=request.action,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                before_json=request.before_json or None,
                after_json=request.after_json or None,
            )
        return audit_pb2.Empty()

    @track_grpc_metrics("audit")
    async def ListAuditEvents(self, request, context):
        async with get_db_context() as db:
            events = await list_audit_events_from_db(
                db,
                entity_type=request.entity_type or None,
                entity_id=request.entity_id or None,
                action=request.action or None,
                limit=request.limit or 200,
            )
            return audit_pb2.AuditEventList(events=[_to_event_response(e) for e in events])

async def serve():
    setup_tracing("audit")
    start_http_server(9105)
    server = grpc.aio.server()
    audit_pb2_grpc.add_AuditServiceServicer_to_server(AuditServiceServicer(), server)

    health_servicer = health.aio.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    await health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port("[::]:50055")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
