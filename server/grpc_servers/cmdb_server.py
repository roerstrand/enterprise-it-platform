import asyncio
import os
import grpc
from prometheus_client import start_http_server

USER_SERVICE_ADDR = os.getenv("USER_SERVICE_ADDR", "localhost:50051")

from protos import cmdb_pb2
from protos import cmdb_pb2_grpc

from protos import user_pb2
from protos import user_pb2_grpc


from repositories.cmdb_repository import (
    create_ci_in_db,
    get_ci_by_id_from_db,
    get_all_cis_from_db,
    create_relationship_in_db,
    get_related_cis_from_db,
    update_ci_in_db,
    delete_ci_from_db
)

from data.database import get_db_context
from observability.grpc_metrics import track_grpc_metrics
from observability.tracing import setup_tracing
from messaging.publisher import publish_event
from google.protobuf.json_format import MessageToDict, ParseDict
from caching.cache import get_cached, set_cached, delete_cached

def _to_ci_response(ci):
    response = cmdb_pb2.CIResponse(
        id=ci.id, name=ci.name, ci_type=ci.ci_type, environment=ci.environment
    )
    if ci.owner_team_id is not None:
        response.owner_team_id = ci.owner_team_id
    if ci.owner_user_id is not None:
        response.owner_user_id = ci.owner_user_id
    return response

class CmdbServiceServicer(cmdb_pb2_grpc.CmdbServiceServicer):

    @track_grpc_metrics("cmdb")
    async def CreateCI(self, request, context):
        async with get_db_context() as db:
            owner_team_id = request.owner_team_id if request.HasField("owner_team_id") else None
            owner_user_id = request.owner_user_id if request.HasField("owner_user_id") else None

            ci = await create_ci_in_db(db, request.name, request.ci_type, request.environment, owner_team_id, owner_user_id)

            try:
                await asyncio.to_thread(publish_event, "cmdb_events", "ci.created", 
                                        {
                                            "id": ci.id, "name": ci.name, "ci_type": ci.ci_type, "environment": ci.environment, "owner_user_id": ci.owner_user_id,
                                        })
            except Exception as e:
                print(f"publish_event misslyckades: {e}")

            try:
                await delete_cached("cis:all")
            except Exception as e:
                print(f"delete_cached misslyckades: {e}")
            return _to_ci_response(ci)
        
    @track_grpc_metrics("cmdb")
    async def GetCI(self, request, context):
        cache_key = f"ci:{request.id}"
        cached = await get_cached(cache_key)
        if cached is not None:
            return ParseDict(cached, cmdb_pb2.CIResponse())

        async with get_db_context() as db:
            ci = await get_ci_by_id_from_db(db, request.id)
            if ci:
                response = _to_ci_response(ci)
                await set_cached(cache_key, MessageToDict(response))
                return response
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("CI {request.id} not found")
            return cmdb_pb2.CIResponse()

    @track_grpc_metrics("cmdb")
    async def ListCIs(self, request, context):
        cache_key = "cis:all"
        cached = await get_cached(cache_key)
        if cached is not None:
            return ParseDict(cached, cmdb_pb2.CIList())

        async with get_db_context() as db:
            cis = await get_all_cis_from_db(db)
            response = cmdb_pb2.CIList(cis=[_to_ci_response(ci) for ci in cis])
            return response

    @track_grpc_metrics("cmdb")
    async def CreateRelationship(self, request, context):
        async with get_db_context() as db:
            relationship = await create_relationship_in_db(
                db, request.source_ci_id, request.target_ci_id, request.relationship_type
            )

            await delete_cached(f"related_cis:{relationship.source_ci_id}")
            await delete_cached(f"related_cis:{relationship.target_ci_id}")

            return cmdb_pb2.RelationshipResponse(
                id=relationship.id,
                source_ci_id=relationship.source_ci_id,
                target_ci_id=relationship.target_ci_id,
                relationship_type=relationship.relationship_type,
            )

    @track_grpc_metrics("cmdb")
    async def GetRelatedCIs(self, request, context):
        cache_key = f"related_cis: {request.id}"
        cached = await get_cached(cache_key)
        if cached is not None:
            return ParseDict(cached, cmdb_pb2.CIList())

        async with get_db_context() as db:
            cis = await get_related_cis_from_db(db, request.id)
            response = cmdb_pb2.CIList(cis=[_to_ci_response(ci) for ci in cis])
            await set_cached(cache_key, MessageToDict(response))
            return response

    @track_grpc_metrics("cmdb")
    async def GetCIWithOwner(self, request, context):
        cache_key = f"ci_with_owner: {request.id}"
        cached = await get_cached(cache_key)
        if cached is not None:
            return ParseDict(cached, cmdb_pb2.CIWithOwnerResponse())

        async with get_db_context() as db:
            ci = await get_ci_by_id_from_db(db, request.id)

            if not ci:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"CI {request.id} not found")
                return cmdb_pb2.CIWithOwnerResponse()

            ci_response = _to_ci_response(ci)

            if ci.owner_user_id is None:
                response = cmdb_pb2.CIWithOwnerResponse(ci=ci_response)
                await set_cached(cache_key, MessageToDict(response))
                return response

            async with grpc.aio.insecure_channel(USER_SERVICE_ADDR) as channel:
                user_stub = user_pb2_grpc.UserServiceStub(channel)
                user = await user_stub.GetUserById(user_pb2.UserIdRequest(id=ci.owner_user_id))

            response = cmdb_pb2.CIWithOwnerResponse(
                ci=ci_response, owner_name=user.name, owner_email=user.email
            )
            await set_cached(cache_key, MessageToDict(response))
            return response

    @track_grpc_metrics("cmdb")
    async def UpdateCI(self, request, context):
        async with get_db_context() as db:
            owner_team_id = request.owner_team_id if request.HasField("owner_team_id") else None
            owner_user_id = request.owner_user_id if request.HasField("owner_user_id") else None
            ci = await update_ci_in_db(db, request.id, request.name, request.ci_type, request.environment, owner_team_id, owner_user_id)
            if not ci:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"CI {request.id} not found")
                return cmdb_pb2.CIResponse()

            try:
                await delete_cached(f"ci:{request.id}")
                await delete_cached(f"ci_with_owner:{request.id}")
                await delete_cached("cis:all")
            except Exception as e:
                print(f"delete_cached misslyckades: {e}")

            return _to_ci_response(ci)

    @track_grpc_metrics("cmdb")
    async def DeleteCI(self, request, context):
        async with get_db_context() as db:
            deleted = await delete_ci_from_db(db, request.id)
            if not deleted:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"CI {request.id} not found")

            try:
                await delete_cached(f"ci:{request.id}")
                await delete_cached(f"ci_with_owner:{request.id}")
                await delete_cached("cis:all")
            except Exception as e:
                print(f"delete_cached misslyckades: {e}")

            return cmdb_pb2.Empty()

async def serve():
    setup_tracing("cmdb")
    start_http_server(9102)
    server = grpc.aio.server()
    cmdb_pb2_grpc.add_CmdbServiceServicer_to_server(CmdbServiceServicer(), server)
    server.add_insecure_port("[::]:50052")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
