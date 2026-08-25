import asyncio

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse

from grpc_clients.user_client import (
    list_users, create_user, login, update_user_role,
    UserServiceUnavailable, InvalidCredentials, RoleNotFound, InvalidRole, EmailAlreadyExists, RoleUpdateForbidden
)
from grpc_clients.incident_client import (
    list_incidents, get_incident_with_ci, get_incident, create_incident, add_incident_update, get_incident_updates,
    accept_suggested_severity, accept_suggested_status, update_incident, update_incident_status,
    update_incident_severity, assign_incident, delete_incident,
    link_change, unlink_change, get_linked_change_ids, get_incident_ids_for_change,
    IncidentServiceUnavailable, IncidentNotFound, InvalidIncidentInput,
)
from grpc_clients.cmdb_client import (
    list_cis, get_ci_with_owner, get_related_cis, create_ci, update_ci, delete_ci,
    CmdbServiceUnavailable, CINotFound,
)
from grpc_clients.change_client import list_changes, get_change, create_change, approve_change, ChangeServiceUnavailable, ChangeNotFound, InvalidChangeInput
from grpc_clients.audit_client import list_audit_events, AuditServiceUnavailable
from schemas.user_create import UserCreateSchema
from schemas.user_login import UserLoginSchema
from schemas.user_role_update import UserRoleUpdateSchema
from schemas.incident_create import IncidentCreateSchema
from schemas.incident_update_create import IncidentUpdateCreateSchema
from schemas.incident_edit import IncidentEditSchema
from schemas.incident_status_update import IncidentStatusUpdateSchema
from schemas.incident_severity_update import IncidentSeverityUpdateSchema
from schemas.incident_assignee_update import IncidentAssigneeUpdateSchema
from schemas.incident_change_link import IncidentChangeLinkSchema
from schemas.ci_create import CICreateSchema
from schemas.ci_edit import CIEditSchema
from schemas.change_create import ChangeCreateSchema

from auth.dependencies import get_current_user, require_roles, CurrentUser, oauth2_schema

router = APIRouter(prefix="/demo")

# Viewer/Operator/Admin får alla läsa (get_current_user). Bara Admin/Operator får mutera CI/incident/change
# (require_roles). RBAC:n är server-side här - Angular döljer/inaktiverar bara knappar, den enforcear inget.
manage = require_roles("admin", "operator")
admin_only = require_roles("admin")

@router.get("")
def demo_page():
    return FileResponse("static/demo/index.html", headers={"Cache-Control": "no-store"})

@router.get("/api/users")
async def api_list_users(user: CurrentUser = Depends(get_current_user)):
    # Alla inloggade behöver kunna slå upp namn (t.ex. författare i en incident-tidslinje),
    # men bara Admin får se hela katalogen med email+roll - annars läcker varje användares
    # email till t.ex. en Viewer bara för att de öppnar en annan sidas nätverksflik.
    try:
        users = await list_users()
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")
    if user.role == "admin":
        return users
    return [{"id": u["id"], "name": u["name"]} for u in users]

@router.post("/api/users")
async def api_create_user(user: UserCreateSchema):
    # Öppen självregistrering - alltid roll "viewer" (se user_server.CreateUser), ingen auth krävs.
    try:
        return await create_user(user.name, user.email, user.password)
    except EmailAlreadyExists:
        raise HTTPException(status_code=409, detail="Email is already registered")
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.put("/api/users/{user_id}/role")
async def api_update_user_role(user_id: int, body: UserRoleUpdateSchema, admin: CurrentUser = Depends(admin_only), token: str = Depends(oauth2_schema)):
    try:
        return await update_user_role(user_id, body.role, token)
    except RoleNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except InvalidRole as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RoleUpdateForbidden:
        raise HTTPException(status_code=403, detail="A valid admin token is required to change roles")
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/login")
async def api_login(credentials: UserLoginSchema):
    try:
        return await login(credentials.email, credentials.password)
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC services is down")

@router.get("/api/me")
def api_me(user: CurrentUser = Depends(get_current_user)):
    return user.to_dict()

@router.get("/api/incidents")
async def api_list_incidents(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    assignee_user_id: int | None = Query(default=None),
    unassigned_only: bool = Query(default=False),
    ci_id: int | None = Query(default=None),
    sla_state: str | None = Query(default=None),
    search: str | None = Query(default=None),
    created_after: str | None = Query(default=None),
    created_before: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
):
    try:
        return await list_incidents(
            status=status, severity=severity, assignee_user_id=assignee_user_id,
            unassigned_only=unassigned_only, ci_id=ci_id, sla_state=sla_state, search=search,
            created_after=created_after, created_before=created_before,
            sort_by=sort_by, sort_dir=sort_dir, page=page, page_size=page_size,
        )
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/incidents/{incident_id}")
async def api_get_incident(incident_id: int, user: CurrentUser = Depends(get_current_user)):
    try:
        return await get_incident_with_ci(incident_id)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/incidents")
async def api_create_incident(incident: IncidentCreateSchema, user: CurrentUser = Depends(manage)):
    try:
        return await create_incident(incident.title, incident.description, incident.severity, incident.ci_id, user.id, user.email)
    except InvalidIncidentInput as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/incidents/{incident_id}/updates")
async def api_add_incident_update(incident_id: int, update: IncidentUpdateCreateSchema, user: CurrentUser = Depends(manage)):
    try:
        return await add_incident_update(incident_id, update.text, user.id, user.email)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/incidents/{incident_id}/updates")
async def api_list_incident_updates(incident_id: int, user: CurrentUser = Depends(get_current_user)):
    try:
        return await get_incident_updates(incident_id)
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/incidents/{incident_id}/accept-severity")
async def api_accept_incident_severity(incident_id: int, user: CurrentUser = Depends(manage)):
    try:
        return await accept_suggested_severity(incident_id, user.id, user.email)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidIncidentInput as e:
        # Latent idag (AcceptSuggestedSeverity kastar aldrig detta ännu) men symmetrisk med
        # accept-status nedan - samma anropsform, samma audit-mönster, ska hanteras likadant.
        raise HTTPException(status_code=409, detail=str(e))
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/incidents/{incident_id}/accept-status")
async def api_accept_incident_status(incident_id: int, user: CurrentUser = Depends(manage)):
    try:
        return await accept_suggested_status(incident_id, user.id, user.email)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidIncidentInput as e:
        raise HTTPException(status_code=409, detail=str(e))
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.put("/api/incidents/{incident_id}")
async def api_update_incident(incident_id: int, incident: IncidentEditSchema, user: CurrentUser = Depends(manage)):
    try:
        return await update_incident(incident_id, incident.title, incident.description, incident.severity, incident.ci_id, user.id, user.email)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidIncidentInput as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.put("/api/incidents/{incident_id}/status")
async def api_update_incident_status(incident_id: int, body: IncidentStatusUpdateSchema, user: CurrentUser = Depends(manage)):
    try:
        return await update_incident_status(incident_id, body.status, user.id, user.email)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidIncidentInput as e:
        # Ogiltig lifecycle-övergång (t.ex. open -> resolved) - 409 Conflict, inte 400
        raise HTTPException(status_code=409, detail=str(e))
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.put("/api/incidents/{incident_id}/severity")
async def api_update_incident_severity(incident_id: int, body: IncidentSeverityUpdateSchema, user: CurrentUser = Depends(manage)):
    try:
        return await update_incident_severity(incident_id, body.severity, user.id, user.email)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidIncidentInput as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.put("/api/incidents/{incident_id}/assignee")
async def api_assign_incident(incident_id: int, body: IncidentAssigneeUpdateSchema, user: CurrentUser = Depends(manage)):
    try:
        return await assign_incident(incident_id, body.assignee_user_id, user.id, user.email)
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except InvalidIncidentInput as e:
        # "User X not found" (ogiltigt assignee_user_id) - 400, inte 409, det är inputvalidering
        raise HTTPException(status_code=400, detail=str(e))
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/incidents/{incident_id}/changes")
async def api_get_linked_changes(incident_id: int, user: CurrentUser = Depends(get_current_user)):
    try:
        change_ids = await get_linked_change_ids(incident_id)
        changes = await asyncio.gather(*(get_change(cid) for cid in change_ids), return_exceptions=True)
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")
    # En länkad change kan i teorin ha försvunnit ur ChangeService - hoppa över den posten istället
    # för att låta hela listan misslyckas
    return [c for c in changes if not isinstance(c, Exception)]

@router.post("/api/incidents/{incident_id}/changes")
async def api_link_change(incident_id: int, body: IncidentChangeLinkSchema, user: CurrentUser = Depends(manage)):
    try:
        await get_change(body.change_id)
    except ChangeNotFound:
        raise HTTPException(status_code=404, detail=f"Change {body.change_id} not found")
    except ChangeServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")
    try:
        await link_change(incident_id, body.change_id, user.id, user.email)
        return {"linked": body.change_id}
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.delete("/api/incidents/{incident_id}/changes/{change_id}")
async def api_unlink_change(incident_id: int, change_id: int, user: CurrentUser = Depends(manage)):
    try:
        await unlink_change(incident_id, change_id, user.id, user.email)
        return {"unlinked": change_id}
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.delete("/api/incidents/{incident_id}")
async def api_delete_incident(incident_id: int, user: CurrentUser = Depends(manage)):
    try:
        await delete_incident(incident_id, user.id, user.email)
        return {"deleted": incident_id}
    except IncidentNotFound:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/cis")
async def api_list_cis(user: CurrentUser = Depends(get_current_user)):
    try:
        return await list_cis()
    except CmdbServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/cis/{ci_id}")
async def api_get_ci(ci_id: int, user: CurrentUser = Depends(get_current_user)):
    # Aggregerar CMDB (ägare, relaterade CI:n) + Incident + Change + Audit i gatewayen istället för
    # att duplicera data mellan tjänster - varje tjänst förblir källan till sin egen domän, precis
    # som GetIncidentWithCI redan gör i motsatt riktning (incident -> CI-info).
    try:
        ci_task = get_ci_with_owner(ci_id)
        related_task = get_related_cis(ci_id)
        incidents_task = list_incidents(ci_id=ci_id, page_size=100, sort_by="created_at", sort_dir="desc")
        changes_task = list_changes()
        audit_task = list_audit_events(entity_type="ci", entity_id=str(ci_id), limit=50)

        ci, related, incidents_result, all_changes, audit_events = await asyncio.gather(
            ci_task, related_task, incidents_task, changes_task, audit_task
        )
    except CINotFound:
        raise HTTPException(status_code=404, detail=f"CI {ci_id} not found")
    except (CmdbServiceUnavailable, IncidentServiceUnavailable, ChangeServiceUnavailable, AuditServiceUnavailable):
        raise HTTPException(status_code=503, detail="gRPC service is down")

    incidents = incidents_result["incidents"]
    changes = [c for c in all_changes if c["ci_id"] == ci_id]

    return {
        **ci,
        "related_cis": related,
        "incidents": incidents,
        "active_incidents": [i for i in incidents if i["status"] not in ("resolved", "closed")],
        "changes": changes,
        "audit_events": audit_events,
    }

@router.post("/api/cis")
async def api_create_ci(ci: CICreateSchema, user: CurrentUser = Depends(manage)):
    try:
        return await create_ci(ci.name, ci.ci_type, ci.environment, ci.owner_user_id, user.id, user.email)
    except CmdbServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.put("/api/cis/{ci_id}")
async def api_update_ci(ci_id: int, ci: CIEditSchema, user: CurrentUser = Depends(manage)):
    try:
        return await update_ci(ci_id, ci.name, ci.ci_type, ci.environment, ci.owner_user_id, user.id, user.email)
    except CmdbServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.delete("/api/cis/{ci_id}")
async def api_delete_ci(ci_id: int, user: CurrentUser = Depends(manage)):
    try:
        await delete_ci(ci_id, user.id, user.email)
        return {"deleted": ci_id}
    except CmdbServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/changes")
async def api_list_changes(user: CurrentUser = Depends(get_current_user)):
    try:
        return await list_changes()
    except ChangeServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/changes/{change_id}")
async def api_get_change(change_id: int, user: CurrentUser = Depends(get_current_user)):
    try:
        change = await get_change(change_id)
        incident_ids = await get_incident_ids_for_change(change_id)
        incidents = await asyncio.gather(*(get_incident(iid) for iid in incident_ids), return_exceptions=True)
    except ChangeNotFound:
        raise HTTPException(status_code=404, detail=f"Change {change_id} not found")
    except (ChangeServiceUnavailable, IncidentServiceUnavailable):
        raise HTTPException(status_code=503, detail="gRPC service is down")
    return {
        **change,
        "related_incidents": [i for i in incidents if not isinstance(i, Exception)],
    }

@router.post("/api/changes")
async def api_create_change(change: ChangeCreateSchema, user: CurrentUser = Depends(manage)):
    try:
        return await create_change(change.title, change.description, change.risk_level, change.ci_id, user.id, user.email)
    except ChangeServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/changes/{change_id}/approve")
async def api_approve_change(change_id: int, user: CurrentUser = Depends(manage)):
    try:
        return await approve_change(change_id, user.id, user.email)
    except ChangeNotFound:
        raise HTTPException(status_code=404, detail=f"Change {change_id} not found")
    except InvalidChangeInput as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ChangeServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/audit")
async def api_list_audit_events(
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=200, le=500),
    admin: CurrentUser = Depends(admin_only),
):
    try:
        return await list_audit_events(entity_type, entity_id, action, limit)
    except AuditServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")
