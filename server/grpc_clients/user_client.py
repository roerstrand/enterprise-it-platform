import os
import grpc
from protos import user_pb2
from protos import user_pb2_grpc

USER_SERVICE_ADDR = os.getenv("USER_SERVICE_ADDR", "localhost:50051")

_stub = None

def _get_stub():
    # Lazy: skapas första gången den faktiskt behövs, inuti den då körande event-loopen
    # (inte vid modul-import, då binder grpc.aio kanalen till fel loop under uvicorn)
    global _stub
    if _stub is None:
        channel = grpc.aio.insecure_channel(USER_SERVICE_ADDR)
        _stub = user_pb2_grpc.UserServiceStub(channel)
    return _stub

class UserServiceUnavailable(Exception):
    pass

class InvalidCredentials(Exception):
    pass

class RoleNotFound(Exception):
    pass

class InvalidRole(Exception):
    pass

class EmailAlreadyExists(Exception):
    pass

async def list_users():
    try:
        response = await _get_stub().GetAllUsers(user_pb2.Empty())
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise UserServiceUnavailable(str(e))
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in response.users]

async def create_user(name: str, email: str, password: str):
    try:
        response = await _get_stub().CreateUser(user_pb2.CreateUserRequest(name=name, email=email, password=password))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.ALREADY_EXISTS:
            raise EmailAlreadyExists(str(e))
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise UserServiceUnavailable(str(e))
    return {"id": response.id, "name": response.name, "email": response.email, "role": response.role}

async def login(email: str, password: str):
    try:
        response = await _get_stub().Login(user_pb2.LoginRequest(email=email, password=password))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            raise InvalidCredentials(str(e))
        print(f"gRPC-error: {e.code()} - {e.details()}")
        raise UserServiceUnavailable(str(e))
    return {"access_token": response.access_token, "token_type": response.token_type}

async def update_user_role(user_id: int, role: str):
    try:
        response = await _get_stub().UpdateUserRole(user_pb2.UpdateUserRoleRequest(id=user_id, role=role))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise RoleNotFound(str(e))
        if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
            raise InvalidRole(str(e))
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise UserServiceUnavailable(str(e))
    return {"id": response.id, "name": response.name, "email": response.email, "role": response.role}

