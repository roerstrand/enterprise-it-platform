from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse

from grpc_clients.user_client import (
    list_users, create_user, login, update_user_role,
    UserServiceUnavailable, InvalidCredentials, RoleNotFound, InvalidRole, EmailAlreadyExists,
)
from grpc_clients.incident_client import (
    list_incidents, get_incident_with_ci, create_incident, add_incident_update, get_incident_updates,
    accept_suggested_severity, accept_suggested_status, update_incident, update_incident_status,
    update_incident_severity, delete_incident,
    IncidentServiceUnavailable, IncidentNotFound, InvalidIncidentInput,
)
from grpc_clients.cmdb_client import list_cis, create_ci, update_ci, delete_ci, CmdbServiceUnavailable
from grpc_clients.change_client import list_changes, create_change, approve_change, ChangeServiceUnavailable
from grpc_clients.audit_client import list_audit_events, AuditServiceUnavailable
from schemas.user_create import UserCreateSchema
from schemas.user_login import UserLoginSchema
from schemas.user_role_update import UserRoleUpdateSchema
from schemas.incident_create import IncidentCreateSchema
from schemas.incident_update_create import IncidentUpdateCreateSchema
from schemas.incident_edit import IncidentEditSchema
from schemas.incident_status_update import IncidentStatusUpdateSchema
from schemas.incident_severity_update import IncidentSeverityUpdateSchema
from schemas.ci_create import CICreateSchema
from schemas.ci_edit import CIEditSchema
from schemas.change_create import ChangeCreateSchema

from auth.dependencies import get_current_user, require_roles, CurrentUser

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
async def api_update_user_role(user_id: int, body: UserRoleUpdateSchema, admin: CurrentUser = Depends(admin_only)):
    try:
        return await update_user_role(user_id, body.role)
    except RoleNotFound:
        raise HTTPException(status_code=404, detail="User not found")
    except InvalidRole as e:
        raise HTTPException(status_code=400, detail=str(e))
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
async def api_list_incidents(user: CurrentUser = Depends(get_current_user)):
    try:
        return await list_incidents()
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
