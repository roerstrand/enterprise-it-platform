import os
import grpc
from protos import incident_pb2
from protos import incident_pb2_grpc

INCIDENT_SERVICE_ADDR = os.getenv("INCIDENT_SERVICE_ADDR", "localhost:50053")

_stub = None

def _get_stub():
    global _stub
    if _stub is None:
        channel = grpc.aio.insecure_channel(INCIDENT_SERVICE_ADDR)
        _stub = incident_pb2_grpc.IncidentServiceStub(channel)
    return _stub

class IncidentServiceUnavailable(Exception):
    pass

def _to_dict(incident):
    return {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "status": incident.status,
        "severity": incident.severity,
        "ci_id": incident.ci_id,
        "ai_summary": incident.ai_summary,
        "ai_summary_status": incident.ai_summary_status,
        "ai_suggested_severity": incident.ai_suggested_severity,
        "ai_suggested_status": incident.ai_suggested_status,
    }

async def list_incidents():
    try:
        response = await _get_stub().ListIncidents(incident_pb2.Empty())
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise IncidentServiceUnavailable(str(e))
    return [_to_dict(i) for i in response.incidents]

async def create_incident(title: str, description: str, severity: str, ci_id: int):
    try:
        response = await _get_stub().CreateIncident(incident_pb2.CreateIncidentRequest(
            title=title, description=description, severity=severity, ci_id=ci_id
        ))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise IncidentServiceUnavailable(str(e))
    return _to_dict(response)

async def add_incident_update(incident_id: int, text: str):
    try:
        response = await _get_stub().AddIncidentUpdate(incident_pb2.AddIncidentUpdateRequest(
            incident_id=incident_id, text=text
        ))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise IncidentServiceUnavailable(str(e))
    return _to_dict(response)

async def accept_suggested_severity(incident_id: int):
    try:
        response = await _get_stub().AcceptSuggestedSeverity(incident_pb2.IncidentIdRequest(id=incident_id))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise IncidentServiceUnavailable(str(e))
    return _to_dict(response)

async def accept_suggested_status(incident_id: int):
    try:
        response = await _get_stub().AcceptSuggestedStatus(incident_pb2.IncidentIdRequest(id=incident_id))
    except grpc.RpcError as e:
        print(f"gRPC-fel: {e.code()} {e.details()}")
        raise IncidentServiceUnavailable(str(e))
    return _to_dict(response)

