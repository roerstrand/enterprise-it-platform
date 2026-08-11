import os
import grpc
from protos import change_pb2
from protos import change_pb2_grpc

CHANGE_SERVICE_ADDR = os.getenv("CHANGE_SERVICE_ADDR", "localhost:50054")

_stub = None

def _get_stub():
    global _stub
    if _stub is None:
        channel = grpc.aio.insecure_channel(CHANGE_SERVICE_ADDR)
        _stub = change_pb2_grpc.ChangeServiceStub(channel)
    return _stub

class ChangeServiceUnavailable(Exception):
    pass

def _to_dict(change):
    return {
        "id": change.id,
        "title": change.title,
        "description": change.description,
        "status": change.status,
        "risk_level": change.risk_level,
        "ci_id": change.ci_id,
    }

async def list_changes():
    try:
        response = await _get_stub().ListChanges(change_pb2.Empty())
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise ChangeServiceUnavailable(str(e))
    return [_to_dict(c) for c in response.changes]

async def create_change(title: str, description: str, risk_level: str, ci_id: int):
    try:
        response = await _get_stub().CreateChange(change_pb2.CreateChangeRequest(
            title=title, description=description, risk_level=risk_level, ci_id=ci_id
        ))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise ChangeServiceUnavailable(str(e))
    return _to_dict(response)

async def approve_change(change_id: int):
    try:
        response = await _get_stub().ApproveChange(change_pb2.ChangeIdRequest(id=change_id))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise ChangeServiceUnavailable(str(e))
    return _to_dict(response)
