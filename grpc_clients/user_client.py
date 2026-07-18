import grpc
from protos import user_pb2
from protos import user_pb2_grpc

channel = grpc.insecure_channel("localhost:50051")
stub = user_pb2_grpc.UserServiceStub(channel)

class UserServiceUnavailable(Exception):
    pass

def list_users():
    try:
        response = stub.GetAllUsers(user_pb2.Empty())
    except grpc.RpcError as e:
        raise UserServiceUnavailable(str(e))
    return [{"id": u.id, "name": u.name, "email": u.email} for u in response.users]

def create_user(name: str, email: str, password: str):
    try:
        response = stub.CreateUser(user_pb2.CreateUserRequest(name=name, email=email, password=password))
    except grpc.RpcError as e:
        raise UserServiceUnavailable(str(e))
    return {"id": response.id, "name": response.name, "email": response.email}