import os
import grpc
from protos import cmdb_pb2
from protos import cmdb_pb2_grpc

CMDB_SERVICE_ADDR = os.getenv("CMDB_SERVICE_ADDR", "localhost:50052")

_stub = None

def _get_stub():
    global _stub
    if _stub is None:
        channel = grpc.aio.insecure_channel(CMDB_SERVICE_ADDR)
        _stub = cmdb_pb2_grpc.CmdbServiceStub(channel)
    return _stub

class CmdbServiceUnavailable(Exception):
    pass

class CINotFound(Exception):
    pass

def _to_dict(ci):
    return {
        "id": ci.id,
        "name": ci.name,
        "ci_type": ci.ci_type,
        "environment": ci.environment,
        "owner_team_id": ci.owner_team_id if ci.HasField("owner_team_id") else None,
        "owner_user_id": ci.owner_user_id if ci.HasField("owner_user_id") else None,
    }

async def list_cis():
    try:
        response = await _get_stub().ListCIs(cmdb_pb2.Empty())
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise CmdbServiceUnavailable(str(e))
    return [_to_dict(ci) for ci in response.cis]

async def get_ci_with_owner(ci_id: int):
    try:
        response = await _get_stub().GetCIWithOwner(cmdb_pb2.CIIdRequest(id=ci_id))
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise CINotFound(str(e))
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise CmdbServiceUnavailable(str(e))
    return {
        **_to_dict(response.ci),
        "owner_name": response.owner_name,
        "owner_email": response.owner_email,
    }

async def get_related_cis(ci_id: int):
    try:
        response = await _get_stub().GetRelatedCIs(cmdb_pb2.CIIdRequest(id=ci_id))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise CmdbServiceUnavailable(str(e))
    return [_to_dict(ci) for ci in response.cis]

async def create_ci(name: str, ci_type: str, environment: str, owner_user_id: int | None = None, actor_user_id: int | None = None, actor_email: str | None = None):
    try:
        request = cmdb_pb2.CreateCIRequest(name=name, ci_type=ci_type, environment=environment, actor_user_id=actor_user_id or 0, actor_email=actor_email or "")
        if owner_user_id is not None:
            request.owner_user_id = owner_user_id
        response = await _get_stub().CreateCI(request)
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise CmdbServiceUnavailable(str(e))
    return _to_dict(response)

async def update_ci(ci_id: int, name: str, ci_type: str, environment: str, owner_user_id: int | None = None, actor_user_id: int | None = None, actor_email: str | None = None):
    try:
        request = cmdb_pb2.UpdateCIRequest(id=ci_id, name=name, ci_type=ci_type, environment=environment, actor_user_id=actor_user_id or 0, actor_email=actor_email or "")
        if owner_user_id is not None:
            request.owner_user_id = owner_user_id
        response = await _get_stub().UpdateCI(request)
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise CmdbServiceUnavailable(str(e))
    return _to_dict(response)

async def delete_ci(ci_id: int, actor_user_id: int | None = None, actor_email: str | None = None):
    try:
        await _get_stub().DeleteCI(cmdb_pb2.CIActionRequest(id=ci_id, actor_user_id=actor_user_id or 0, actor_email=actor_email or ""))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise CmdbServiceUnavailable(str(e))