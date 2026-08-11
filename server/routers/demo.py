from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

from grpc_clients.user_client import list_users, create_user, login, UserServiceUnavailable, InvalidCredentials
from grpc_clients.incident_client import list_incidents, create_incident, add_incident_update, IncidentServiceUnavailable
from grpc_clients.cmdb_client import list_cis, create_ci, CmdbServiceUnavailable
from grpc_clients.change_client import list_changes, create_change, approve_change, ChangeServiceUnavailable
from schemas.user_create import UserCreateSchema
from schemas.user_login import UserLoginSchema
from schemas.incident_create import IncidentCreateSchema
from schemas.incident_update_create import IncidentUpdateCreateSchema
from schemas.ci_create import CICreateSchema
from schemas.change_create import ChangeCreateSchema

from auth.dependencies import get_current_user

router = APIRouter(prefix="/demo")

@router.get("")
def demo_page():
    return FileResponse("static/demo/index.html", headers={"Cache-Control": "no-store"})

@router.get("/api/users")
async def api_list_users():
    try:
        return await list_users()
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/users")
async def api_create_user(user: UserCreateSchema):
    try:
        return await create_user(user.name, user.email, user.password)
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
def api_me(user: dict = Depends(get_current_user)):
    return user

@router.get("/api/incidents")
async def api_list_incidents():
    try:
        return await list_incidents()
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/incidents")
async def api_create_incident(incident: IncidentCreateSchema):
    try:
        return await create_incident(incident.title, incident.description, incident.severity, incident.ci_id)
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/incidents/{incident_id}/updates")
async def api_add_incident_update(incident_id: int, update: IncidentUpdateCreateSchema):
    try:
        return await add_incident_update(incident_id, update.text)
    except IncidentServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/cis")
async def api_list_cis():
    try:
        return await list_cis()
    except CmdbServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/cis")
async def api_create_ci(ci: CICreateSchema):
    try:
        return await create_ci(ci.name, ci.ci_type, ci.environment, ci.owner_user_id)
    except CmdbServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.get("/api/changes")
async def api_list_changes():
    try:
        return await list_changes()
    except ChangeServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/changes")
async def api_create_change(change: ChangeCreateSchema):
    try:
        return await create_change(change.title, change.description, change.risk_level, change.ci_id)
    except ChangeServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

@router.post("/api/changes/{change_id}/approve")
async def api_approve_change(change_id: int):
    try:
        return await approve_change(change_id)
    except ChangeServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")

