import asyncio
import os
import grpc
from datetime import datetime, timezone
from prometheus_client import start_http_server

CMDB_SERVICE_ADDR = os.getenv("CMDB_SERVICE_ADDR", "localhost:50052")
USER_SERVICE_ADDR = os.getenv("USER_SERVICE_ADDR", "localhost:50051")

from protos import incident_pb2, incident_pb2_grpc, cmdb_pb2, cmdb_pb2_grpc, user_pb2, user_pb2_grpc

from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from repositories.incident_repository import (
    create_incident_in_db,
    get_incident_by_id_from_db,
    list_incidents_filtered_from_db,
    update_incident_ai_summary,
    mark_incident_ai_summary_failed,
    update_incident_ai_suggested_severity,
    update_incident_ai_suggested_status,
    accept_incident_suggested_severity,
    accept_incident_suggested_status,
    update_incident_in_db,
    update_incident_status_in_db,
    update_incident_severity_in_db,
    update_incident_assignee_in_db,
    delete_incident_from_db,
)

from repositories.incident_update_repository import create_incident_update_in_db, get_updates_for_incident_from_db
from repositories.incident_change_link_repository import (
    link_change_in_db,
    unlink_change_in_db,
    get_change_ids_for_incident,
    get_incident_ids_for_change,
)

from data.database import get_db_context
from observability.grpc_metrics import track_grpc_metrics
from observability.tracing import setup_tracing
from ai.foundry_client import generate_incident_summary, classify_incident_severity, classify_incident_status
from domain.incident_lifecycle import validate_transition, validate_severity, InvalidStatusTransition, InvalidSeverity
from domain.sla import compute_sla
from grpc_clients.audit_client import record_audit_event

def _to_incident_response(incident):
    sla = compute_sla(
        incident.created_at, incident.severity, incident.first_response_at, incident.resolved_at, incident.status
    )
    return incident_pb2.IncidentResponse(
        id=incident.id, title=incident.title, description=incident.description,
        status=incident.status, severity=incident.severity, ci_id=incident.ci_id, ai_summary=incident.ai_summary or "",
        ai_summary_status=incident.ai_summary_status, ai_suggested_severity=incident.ai_suggested_severity or "", ai_suggested_status=incident.ai_suggested_status or "",
        created_at=incident.created_at.isoformat(), updated_at=incident.updated_at.isoformat(),
        assignee_user_id=incident.assignee_user_id or 0,
        sla_response_deadline=sla["response_deadline"].isoformat(),
        sla_resolution_deadline=sla["resolution_deadline"].isoformat(),
        sla_first_response_at=incident.first_response_at.isoformat() if incident.first_response_at else "",
        sla_resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else "",
        sla_response_breached=sla["response_breached"],
        sla_resolution_breached=sla["resolution_breached"],
        sla_state=sla["state"],
        sla_remaining_seconds=sla["remaining_seconds"],
    )

def _parse_iso(value: str):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None

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
        created_after = _parse_iso(request.created_after)
        created_before = _parse_iso(request.created_before)

        async with get_db_context() as db:
            # sla_state kan inte filtreras i SQL (beräknas dynamiskt) - hämta obeskuret för det fallet
            # och paginera i Python istället. Utan sla_state-filter paginerar SQL:en direkt, som vanligt.
            sla_filter = request.sla_state or None
            page = request.page if request.page > 0 else 1
            page_size = min(request.page_size, 100) if request.page_size > 0 else 25

            incidents, total_count = await list_incidents_filtered_from_db(
                db,
                status=request.status or None,
                severity=request.severity or None,
                assignee_user_id=request.assignee_user_id or None,
                unassigned_only=request.unassigned_only,
                ci_id=request.ci_id or None,
                search=request.search or None,
                created_after=created_after,
                created_before=created_before,
                sort_by=request.sort_by or "created_at",
                sort_dir=request.sort_dir or "desc",
                limit=None if sla_filter else page_size,
                offset=0 if sla_filter else (page - 1) * page_size,
            )
            responses = [_to_incident_response(i) for i in incidents]

        if sla_filter:
            responses = [r for r in responses if r.sla_state == sla_filter]
            total_count = len(responses)
            start = (page - 1) * page_size
            responses = responses[start:start + page_size]

        return incident_pb2.ListIncidentsResponse(
            incidents=responses, total_count=total_count, page=page, page_size=page_size
        )

    @track_grpc_metrics("Incident")
    async def GetIncidentWithCI(self, request, context):
        async with get_db_context() as db:
            incident = await get_incident_by_id_from_db(db, request.id)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")

                return incident_pb2.IncidentWithCIResponse()

            incident_response = _to_incident_response(incident)

            # Best-effort, som CMDB-uppslagen i _generate_and_store_summary/_classify_and_store_status
            # nedan - en kort CMDB-blipp ska inte slå ut hela incident-svaret, bara CI-fälten.
            try:
                async with grpc.aio.insecure_channel(CMDB_SERVICE_ADDR) as channel:
                    cmdb_stub = cmdb_pb2_grpc.CmdbServiceStub(channel)
                    ci_with_owner = await cmdb_stub.GetCIWithOwner(cmdb_pb2.CIIdRequest(id=incident.ci_id))
            except grpc.RpcError as e:
                print(f"[incident_server] CMDB lookup failed for ci_id={incident.ci_id}: {e}")
                return incident_pb2.IncidentWithCIResponse(incident=incident_response)

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
            # Kolla att incidenten finns INNAN update-raden skapas - annars kan ett ogiltigt
            # incident_id fortfarande committa en föräldralös incident_update-rad (ingen FK-constraint
            # stoppar det) trots att anroparen får ett rent 404 tillbaka.
            incident = await get_incident_by_id_from_db(db, request.incident_id)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.incident_id} not found")
                return incident_pb2.IncidentResponse()
            await create_incident_update_in_db(db, request.incident_id, request.text, request.actor_user_id or None)
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

            try:
                # Samma skydd som AcceptSuggestedStatus har mot ogiltiga AI-svar - annars kan
                # ett malformat AI-svar spara en severity utanför SEVERITIES rakt in i DB.
                validate_severity(before.ai_suggested_severity or "")
            except InvalidSeverity as e:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details(str(e))
                return incident_pb2.IncidentResponse()

            before_severity = before.severity
            incident = await accept_incident_suggested_severity(db, request.id)
            if not incident:
                # Race: incidenten togs bort mellan "before"-hämtningen ovan och accept-anropet
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
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
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
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
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
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
                new_status = validate_transition(before.status, request.status)
            except InvalidStatusTransition as e:
                context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
                context.set_details(str(e))
                return incident_pb2.IncidentResponse()

            before_status = before.status
            incident = await update_incident_status_in_db(db, request.id, new_status)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
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
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
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
    async def AssignIncident(self, request, context):
        new_assignee_id = request.assignee_user_id or None
        assignee_name = None
        if new_assignee_id is not None:
            # Validera mot befintliga User Service istället för att lita blint på ett client-skickat id -
            # ingen egen kopia av användardata, precis som CI-ägare redan slås upp mot user-server.
            try:
                async with grpc.aio.insecure_channel(USER_SERVICE_ADDR) as channel:
                    user_stub = user_pb2_grpc.UserServiceStub(channel)
                    user = await user_stub.GetUserById(user_pb2.UserIdRequest(id=new_assignee_id))
                    assignee_name = user.name
            except grpc.RpcError as e:
                if e.code() == grpc.StatusCode.NOT_FOUND:
                    context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                    context.set_details(f"User {new_assignee_id} not found")
                    return incident_pb2.IncidentResponse()
                context.set_code(grpc.StatusCode.UNAVAILABLE)
                context.set_details("User service is down, cannot validate assignee")
                return incident_pb2.IncidentResponse()

        async with get_db_context() as db:
            before = await get_incident_by_id_from_db(db, request.id)
            if not before:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()
            before_assignee = before.assignee_user_id

            incident = await update_incident_assignee_in_db(db, request.id, new_assignee_id)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")
                return incident_pb2.IncidentResponse()

            # Syns i incidentens befintliga uppdateringshistorik utan att bygga en ny UI-yta för det -
            # samma återanvändning som audit_client redan gör för status/severity-ändringar.
            if new_assignee_id is None:
                note = "Unassigned"
            elif before_assignee is None:
                note = f"Assigned to {assignee_name}"
            else:
                note = f"Reassigned to {assignee_name}"
            await create_incident_update_in_db(db, request.id, note, request.actor_user_id or None)

            response = _to_incident_response(incident)

        if before_assignee != new_assignee_id:
            action = "incident.unassigned" if new_assignee_id is None else (
                "incident.assigned" if before_assignee is None else "incident.reassigned"
            )
            await record_audit_event(
                request.actor_user_id or None, request.actor_email or None,
                action, "incident", response.id,
                before={"assignee_user_id": before_assignee}, after={"assignee_user_id": new_assignee_id},
            )
        return response

    @track_grpc_metrics("Incident")
    async def LinkChange(self, request, context):
        async with get_db_context() as db:
            incident = await get_incident_by_id_from_db(db, request.incident_id)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.incident_id} not found")
                return incident_pb2.Empty()
            created = await link_change_in_db(db, request.incident_id, request.change_id, request.actor_user_id or None)

        if created:
            await record_audit_event(
                request.actor_user_id or None, request.actor_email or None,
                "incident.change_linked", "incident", request.incident_id,
                before=None, after={"change_id": request.change_id},
            )
        return incident_pb2.Empty()

    @track_grpc_metrics("Incident")
    async def UnlinkChange(self, request, context):
        async with get_db_context() as db:
            removed = await unlink_change_in_db(db, request.incident_id, request.change_id)

        if removed:
            await record_audit_event(
                request.actor_user_id or None, request.actor_email or None,
                "incident.change_unlinked", "incident", request.incident_id,
                before={"change_id": request.change_id}, after=None,
            )
        return incident_pb2.Empty()

    @track_grpc_metrics("Incident")
    async def GetLinkedChangeIds(self, request, context):
        async with get_db_context() as db:
            change_ids = await get_change_ids_for_incident(db, request.id)
            return incident_pb2.ChangeIdList(change_ids=change_ids)

    @track_grpc_metrics("Incident")
    async def GetIncidentIdsForChange(self, request, context):
        async with get_db_context() as db:
            incident_ids = await get_incident_ids_for_change(db, request.change_id)
            return incident_pb2.IncidentIdList(incident_ids=incident_ids)

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
