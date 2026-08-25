import asyncio
import grpc
from sqlalchemy.exc import IntegrityError

from protos import user_pb2
from protos import user_pb2_grpc

from grpc_health.v1 import health, health_pb2, health_pb2_grpc

from repositories.user_repository import (
    get_all_users_from_db,
    get_user_by_id_from_db,
    create_user_in_db,
    get_user_by_email_from_db,
    update_user_role_in_db,
    any_admin_exists_from_db
)
from auth.security import ROLES, decode_access_token

from data.database import get_db_context

import secrets
from auth.security import hash_password, verify_password, create_access_token

from prometheus_client import start_http_server
from observability.grpc_metrics import track_grpc_metrics
from observability.tracing import setup_tracing

class UserServiceServicer(user_pb2_grpc.UserServiceServicer):

    @track_grpc_metrics("user")
    async def GetAllUsers(self, request, context):
        async with get_db_context() as db:
            users = await get_all_users_from_db(db)
            return user_pb2.UserList(
                users=[user_pb2.UserResponse(id=u.id, name=u.name, email=u.email, role=u.role) for u in users]
            )

    @track_grpc_metrics("user")
    async def GetUserById(self, request, context):
        async with get_db_context() as db:
            user = await get_user_by_id_from_db(db, request.id)
            if user:
                return user_pb2.UserResponse(id=user.id, name=user.name, email=user.email, role=user.role)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"User {request.id} not found")
            return user_pb2.UserResponse()


    @track_grpc_metrics("user")
    async def CreateUser(self, request, context):
        hashed_password = await asyncio.to_thread(hash_password, request.password)
        async with get_db_context() as db:
            # Snabb, vänlig kontroll först - users.email har dessutom en UNIQUE-constraint i DB
            # (se migration 9d4b2f7c1e6a) som är den egentliga garantin mot en kapplöpning här.
            if await get_user_by_email_from_db(db, request.email):
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details(f"Email '{request.email}' is already registered")
                return user_pb2.UserResponse()
            try:
                # Självregistrering är alltid "viewer" - roll kan bara höjas via UpdateUserRole (admin-only i gatewayen)
                user = await create_user_in_db(db, request.name, request.email, hashed_password, role="viewer")
            except IntegrityError:
                await db.rollback()
                context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                context.set_details(f"Email '{request.email}' is already registered")
                return user_pb2.UserResponse()
            return user_pb2.UserResponse(id=user.id, name=user.name, email=user.email, role=user.role)

    @track_grpc_metrics("user")
    async def Login(self, request, context):
        async with get_db_context() as db:
            user = await get_user_by_email_from_db(db, request.email)
            if not user or not await asyncio.to_thread(verify_password, request.password, user.hashed_password):
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Invalid email or password")
                return user_pb2.TokenResponse()
            token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
            return user_pb2.TokenResponse(access_token=token, token_type="bearer")

    @track_grpc_metrics("user")
    async def UpdateUserRole(self, request, context):
        if request.role not in ROLES:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(f"Invalid role '{request.role}', must be one of {ROLES}")
            return user_pb2.UserResponse()
        async with get_db_context() as db:
            if await any_admin_exists_from_db(db):
                metadata = dict(context.invocation_metadata())
                auth_header = metadata.get("authorization", "")
                token = auth_header.removeprefix("Bearer ").strip()
                payload = decode_access_token(token) if token else None
                if payload is None or payload.get("role") != "admin":
                    context.set_code(grpc.StatusCode.PERMISSION_DENIED)
                    context.set_details("A valid admin token is required to change roles")
                    return user_pb2.UserResponse()
    
            user = await update_user_role_in_db(db, request.id, request.role)
            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"User {request.id} not found")
                return user_pb2.UserResponse()
            return user_pb2.UserResponse(id=user.id, name=user.name, email=user.email, role=user.role)

async def serve():
    setup_tracing("user")
    start_http_server(9101)
    server = grpc.aio.server()
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)

    health_servicer = health.aio.HealthServicer()
    health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
    await health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)
    
    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
