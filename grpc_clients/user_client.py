import grpc
from protos import user_pb2
from protos import user_pb2_grpc

channel = grpc.aio.insecure_channel("localhost:50051")
stub = user_pb2_grpc.UserServiceStub(channel)

class UserServiceUnavailable(Exception):
    pass

class InvalidCredentials(Exception):
    pass

async def list_users():
    try:
        response = await stub.GetAllUsers(user_pb2.Empty())
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise UserServiceUnavailable(str(e))
    return [{"id": u.id, "name": u.name, "email": u.email} for u in response.users]

async def create_user(name: str, email: str, password: str):
    try:
        response = await stub.CreateUser(user_pb2.CreateUserRequest(name=name, email=email, password=password))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise UserServiceUnavailable(str(e))
    return {"id": response.id, "name": response.name, "email": response.email}

async def login(email: str, password: str):
    try:
        response = await stub.Login(user_pb2.LoginRequest(email=email, password=password))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.UNAUTHENTICATED:
            raise InvalidCredentials(str(e))
        print(f"gRPC-error: {e.code()} - {e.details()}")
        raise UserServiceUnavailable(str(e))
    return {"access_token": response.access_token, "token_type": response.token_type}

