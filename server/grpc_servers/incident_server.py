import asyncio
import os
import grpc
from prometheus_client import start_http_server

CMDB_SERVICE_ADDR = os.getenv("CMDB_SERVICE_ADDR", "localhost:50052")

from protos import incident_pb2, incident_pb2_grpc, cmdb_pb2, cmdb_pb2_grpc

from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from repositories.incident_repository import (
    create_incident_in_db,
    get_incident_by_id_from_db,
    get_all_incidents_from_db,
    update_incident_ai_summary,
    mark_incident_ai_summary_failed,
    update_incident_ai_suggested_severity,
    update_incident_ai_suggested_status,
    accept_incident_suggested_severity,
    accept_incident_suggested_status,
    update_incident_in_db,
    update_incident_status_in_db,
    update_incident_severity_in_db,
    delete_incident_from_db,
)

from repositories.incident_update_repository import create_incident_update_in_db, get_updates_for_incident_from_db

from data.database import get_db_context
from observability.grpc_metrics import track_grpc_metrics
from observability.tracing import setup_tracing
from ai.foundry_client import generate_incident_summary, classify_incident_severity, classify_incident_status
from domain.incident_lifecycle import validate_transition, validate_severity, InvalidStatusTransition, InvalidSeverity
from grpc_clients.audit_client import record_audit_event

def _to_incident_response(incident):
     return incident_pb2.IncidentResponse(
        id=incident.id, title=incident.title, description=incident.description,
        status=incident.status, severity=incident.severity, ci_id=incident.ci_id, ai_summary=incident.ai_summary or "",
        ai_summary_status=incident.ai_summary_status, ai_suggested_severity=incident.ai_suggested_severity or "", ai_suggested_status=incident.ai_suggested_status or "",
        created_at=incident.created_at.isoformat(), updated_at=incident.updated_at.isoformat()
    )

_background_tasks: set[asyncio.Task] = set()

def _fire_and_forget(coro):
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task

async def _generate_and_store_summary(incident_id, title, description, ci_id):
    ci_name = ci_environment = owner_name = None
    try:
        async with grpc.aio.insecure_channel(CMDB_SERVICE_ADDR) as channel:
            cmdb_stub = cmdb_pb2_grpc.CmdbServiceStub(channel)
            ci_with_owner = await cmdb_stub.GetCIWithOwner(cmdb_pb2.CIIdRequest(id=ci_id))
            ci_name = ci_with_owner.ci.name
            ci_environment = ci_with_owner.ci.environment
            owner_name = ci_with_owner.owner_name
    except grpc.RpcError as e:
        print(f"[incident_server] CMDB lookup failed for ci_id={ci_id}: {e}")

    summary = await asyncio.to_thread(
        generate_incident_summary, title, description, ci_name, ci_environment, owner_name
    )

    suggested_severity = await asyncio.to_thread(
        classify_incident_severity, title, description, ci_name, ci_environment, owner_name
    )

    if suggested_severity:
        async with get_db_context() as db:
            await update_incident_ai_suggested_severity(db, incident_id, suggested_severity)

    if summary:
        async with get_db_context() as db:
            await update_incident_ai_summary(db, incident_id, summary)
    else:
        async with get_db_context() as db:
            await mark_incident_ai_summary_failed(db, incident_id)

async def _classify_and_store_status(incident_id, title, description, ci_id):
    ci_name = ci_environment = owner_name = None
    try:
        async with grpc.aio.insecure_channel(CMDB_SERVICE_ADDR) as channel:
            cmdb_stub = cmdb_pb2_grpc.CmdbServiceStub(channel)
            ci_with_owner = await cmdb_stub.GetCIWithOwner(cmdb_pb2.CIIdRequest(id=ci_id))
            ci_name = ci_with_owner.ci.name
            ci_environment = ci_with_owner.ci.environment
            owner_name = ci_with_owner.owner_name
    except grpc.RpcError as e:
        print(f"[incident server] CMDB lookup failed for ci_id={ci_id}: {e}")

    async with get_db_context() as db:
        updates = await get_updates_for_incident_from_db(db, incident_id)

    suggested_status = await asyncio.to_thread(
        classify_incident_status, title, description, [u.text for u in updates], ci_name, ci_environment, owner_name
    )

    if suggested_status:
        async with get_db_context() as db:
            await update_incident_ai_suggested_status(db, incident_id, suggested_status)


class IncidentServiceServicer(incident_pb2_grpc.IncidentServiceServicer):

    @track_grpc_metrics("Incident")
    async def CreateIncident(self, request, context):
        try:
            severity = validate_severity(request.severity)
        except InvalidSeverity as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return incident_pb2.IncidentResponse()

        async with get_db_context() as db:
            incident = await create_incident_in_db(db, request.title, request.description, severity, request.ci_id)
            response = _to_incident_response(incident)

        await record_audit_event(
            request.actor_user_id or None, request.actor_email or None,
            "incident.created", "incident", incident.id,
            before=None, after={"title": incident.title, "severity": incident.severity, "ci_id": incident.ci_id, "status": incident.status},
        )

        _fire_and_forget(
            _generate_and_store_summary(incident.id, incident.title, incident.description, incident.ci_id)
        )

        return response

    @track_grpc_metrics("Incident")
    async def GetIncident(self, request, context):
        async with get_db_context() as db:
            incident = await get_incident_by_id_from_db(db, request.id)
            if incident:
                return _to_incident_response(incident)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Incident {request.id} not found")
            return incident_pb2.IncidentResponse()

    @track_grpc_metrics("Incident")
    async def ListIncidents(self, request, context):
        async with get_db_context() as db:
            incidents = await get_all_incidents_from_db(db)
            return incident_pb2.IncidentList(incidents=[_to_incident_response(i) for i in incidents])

    @track_grpc_metrics("Incident")
    async def GetIncidentWithCI(self, request, context):
        async with get_db_context() as db:
            incident = await get_incident_by_id_from_db(db, request.id)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")

                return incident_pb2.IncidentWithCIResponse()

            incident_response = _to_incident_response(incident)

            async with grpc.aio.insecure_channel(CMDB_SERVICE_ADDR) as channel:
                cmdb_stub = cmdb_pb2_grpc.CmdbServiceStub(channel)
                ci_with_owner = await cmdb_stub.GetCIWithOwner(cmdb_pb2.CIIdRequest(id=incident.ci_id))

                return incident_pb2.IncidentWithCIResponse(
                incident=incident_response,
                ci_name=ci_with_owner.ci.name,
                ci_environment=ci_with_owner.ci.environment,
                ci_type=ci_with_owner.ci.ci_type,
                owner_name=ci_with_owner.owner_name,
                owner_email=ci_with_owner.owner_email,
            )

    @track_grpc_metrics("Incident")
    async def AddIncidentUpdate(self, request, context):
        async with get_db_context() as db:
            await create_incident_update_in_db(db, request.incident_id, request.text, request.actor_user_id or None)
            incident = await get_incident_by_id_from_db(db, request.incident_id)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.incident_id} not found")
                return incident_pb2.IncidentResponse()
            response = _to_incident_response(incident)

        await record_audit_event(
            request.actor_user_id or None, request.actor_email or None,
            "incident.update_added", "incident", incident.id,
            before=None, after={"text": request.text},
        )

        _fire_and_forget(
            _classify_and_store_status(incident.id, incident.title, incident.description, incident.ci_id)
        )

        return response

    @track_grpc_metrics("Incident")
    async def GetIncidentUpdates(self, request, context):
        async with get_db_context() as db:
            updates = await get_updates_for_incident_from_db(db, request.id)
            return incident_pb2.IncidentUpdateList(updates=[
                incident_pb2.IncidentUpdateResponse(
                    id=u.id, incident_id=u.incident_id, text=u.text,
                    author_user_id=u.author_user_id or 0, created_at=u.created_at.isoformat(),
                )
                for u in updates
            ])

    @track_grpc_metrics("Incident")
    async def AcceptSuggestedSeverity(self, request, context):
        # OBS: allt som läser ORM-attribut (inkl. _to_incident_response, som läser created_at/updated_at)
        # måste ske INNAN "async with"-blocket stängs - annars DetachedInstanceError, session är då stängd.
        async with get_db_context() as db:
            before = await get_incident_by_id_from_db(db, request.id)
            if not before:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
            before_severity = before.severity
            incident = await accept_incident_suggested_severity(db, request.id)
            changed = incident.severity != before_severity
            response = _to_incident_response(incident)

        if changed:
            await record_audit_event(
                request.actor_user_id or None, request.actor_email or None,
                "incident.severity_changed", "incident", response.id,
                before={"severity": before_severity}, after={"severity": response.severity},
            )
        return response

    @track_grpc_metrics("Incident")
    async def AcceptSuggestedStatus(self, request, context):
        async with get_db_context() as db:
            before = await get_incident_by_id_from_db(db, request.id)
            if not before:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()

            try:
                validate_transition(before.status, (before.ai_suggested_status or "").lower())
            except InvalidStatusTransition as e:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details(str(e))
                return incident_pb2.IncidentResponse()

            before_status = before.status
            incident = await accept_incident_suggested_status(db, request.id)
            changed = incident.status != before_status
            response = _to_incident_response(incident)

        if changed:
            await record_audit_event(
                request.actor_user_id or None, request.actor_email or None,
                "incident.status_changed", "incident", response.id,
                before={"status": before_status}, after={"status": response.status},
            )
        return response

    @track_grpc_metrics("Incident")
    async def UpdateIncident(self, request, context):
        try:
            severity = validate_severity(request.severity)
        except InvalidSeverity as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return incident_pb2.IncidentResponse()

        async with get_db_context() as db:
            before = await get_incident_by_id_from_db(db, request.id)
            if not before:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
            before_snapshot = {"title": before.title, "description": before.description, "severity": before.severity, "ci_id": before.ci_id}

            incident = await update_incident_in_db(
                db, request.id, request.title, request.description, severity, request.ci_id
            )
            response = _to_incident_response(incident)

        await record_audit_event(
            request.actor_user_id or None, request.actor_email or None,
            "incident.updated", "incident", response.id,
            before=before_snapshot,
            after={"title": response.title, "description": response.description, "severity": response.severity, "ci_id": response.ci_id},
        )
        return response

    @track_grpc_metrics("Incident")
    async def UpdateIncidentStatus(self, request, context):
        async with get_db_context() as db:
            before = await get_incident_by_id_from_db(db, request.id)
            if not before:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()

            try:
                validate_transition(before.status, request.status)
            except InvalidStatusTransition as e:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details(str(e))
                return incident_pb2.IncidentResponse()

            before_status = before.status
            incident = await update_incident_status_in_db(db, request.id, request.status)
            changed = incident.status != before_status
            response = _to_incident_response(incident)

        if changed:
            await record_audit_event(
                request.actor_user_id or None, request.actor_email or None,
                "incident.status_changed", "incident", response.id,
                before={"status": before_status}, after={"status": response.status},
            )
        return response

    @track_grpc_metrics("Incident")
    async def UpdateIncidentSeverity(self, request, context):
        try:
            severity = validate_severity(request.severity)
        except InvalidSeverity as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return incident_pb2.IncidentResponse()

        async with get_db_context() as db:
            before = await get_incident_by_id_from_db(db, request.id)
            if not before:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
            before_severity = before.severity
            incident = await update_incident_severity_in_db(db, request.id, severity)
            changed = incident.severity != before_severity
            response = _to_incident_response(incident)

        if changed:
            await record_audit_event(
                request.actor_user_id or None, request.actor_email or None,
                "incident.severity_changed", "incident", response.id,
                before={"severity": before_severity}, after={"severity": response.severity},
            )
        return response

    @track_grpc_metrics("Incident")
    async def DeleteIncident(self, request, context):
        async with get_db_context() as db:
            before = await get_incident_by_id_from_db(db, request.id)
            if not before:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.Empty()
            before_snapshot = {"title": before.title, "status": before.status, "severity": before.severity}

            deleted = await delete_incident_from_db(db, request.id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.Empty()

        await record_audit_event(
            request.actor_user_id or None, request.actor_email or None,
            "incident.deleted", "incident", request.id,
            before=before_snapshot,
            after=None,
        )
        return incident_pb2.Empty()


async def serve():
    setup_tracing("incident")
    start_http_server(9103)
    server = grpc.aio.server()
    incident_pb2_grpc.add_IncidentServiceServicer_to_server(IncidentServiceServicer(), server)

    health_servicer = health.aio.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    await health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)

    server.add_insecure_port("[::]:50053")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
