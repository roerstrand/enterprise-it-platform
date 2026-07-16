import grpc
from concurrent import futures

from protos import user_pb2
from protos import user_pb2_grpc

from repositories.user_repository import (
    get_all_users_from_db,
    get_user_by_id_from_db,
    create_user_in_db
)

from data.database import SessionLocal

class UserServiceServicer(user_pb2_grpc.UserServiceServicer):

    def GetAllUsers(self, request, context):
        db = SessionLocal()
        users = get_all_users_from_db(db)
        return user_pb2.UserList(
            users=[user_pb2.UserResponse(id=u.id, name=u.name, email=u.email) for u in users]
        )

    def GetUserById(self, request, context):
        db = SessionLocal()
        user = get_user_by_id_from_db(db, request.id)
        if user:
            return user_pb2.UserResponse(id=user.id, name=user.name, email=user.email)
        context.set_code(grpc.StatusCode.NOT_FOUND)
        context.set_details(f"User {request.id} not found")
        return user_pb2.UserResponse()
                
            
        
    def CreateUser(self, request, context):
        db = SessionLocal()
        user = create_user_in_db(db, request.name, request.email)
        return user_pb2.UserResponse(id=user.id, name=user.name, email=user.email)
    
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
    
