from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from grpc_clients.user_client import list_users, create_user, UserServiceUnavailable
from schemas.user_create import UserCreateSchema

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
    
