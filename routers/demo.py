from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from grpc_clients.user_client import list_users, create_user, login, UserServiceUnavailable, InvalidCredentials
from schemas.user_create import UserCreateSchema
from schemas.user_login import UserLoginSchema

router = APIRouter(prefix="/demo")

@router.get("")
def demo_page():
    return FileResponse("static/demo/index.html")

@router.get("/api/users")
def api_list_users():
    try:
        return list_users()
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")
    
@router.post("/api/users")
def api_create_user(user: UserCreateSchema):
    try:
        return create_user(user.name, user.email, user.password)
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, detail="gRPC service is down")
    
@router.post("/api/login")
def api_login(credentials: UserLoginSchema):
    try:
        return login(credentials.email, credentials.password)
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    except UserServiceUnavailable:
        raise HTTPException(status_code=503, details="gRPC services is down")