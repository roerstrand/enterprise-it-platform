import grpc
from concurrent import futures
from prometheus_client import start_http_server

from protos import incident_pb2, incident_pb2_grpc, cmdb_pb2, cmdb_pb2_grpc

from repositories.incident_repository import (
    create_incident_in_db,
    get_incident_by_id_from_db,
    get_all_incidents_from_db
)

from data.database import get_db_context
from observability.grpc_metrics import track_grpc_metrics
from observability.tracing import setup_tracing

def _to_incident_response(incident):
     return incident_pb2.IncidentResponse(
        id=incident.id, title=incident.title, description=incident.description,
        status=incident.status, severity=incident.severity, ci_id=incident.ci_id
    )

class IncidentServiceServicer(incident_pb2_grpc.IncidentServiceServicer):

    @track_grpc_metrics("Incident")
    def CreateIncident(self, request, context):
        with get_db_context() as db:
            incident = create_incident_in_db(db, request.title, request.description, request.severity, request.ci_id)
            return _to_incident_response(incident)

    @track_grpc_metrics("Incident")
    def GetIncident(self, request, context):
        with get_db_context() as db:
            incident = get_incident_by_id_from_db(db, request.id)
            if incident:
                return _to_incident_response(incident)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"Incident {request.id} not found")
            return incident_pb2.IncidentResponse()

    @track_grpc_metrics("Incident")
    def ListIncidents(self, request, context):
        with get_db_context() as db:
            incidents = get_all_incidents_from_db(db)
            return incident_pb2.IncidentList(incidents={_to_incident_response(i) for i in incidents})

    @track_grpc_metrics("Incident")
    def GetIncidentWithCI(self, request, context):
        with get_db_context() as db:
            incident = get_incident_by_id_from_db(db, request.id)
            if not incident:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Incident {request.id} not found")

                return incident_pb2.IncidentWithCIResponse()

            incident_response = _to_incident_response(incident)

            with grpc.insecure_channel("localhost:50052") as channel:
                cmdb_stub = cmdb_pb2_grpc.CmdbServiceStub(channel)
                ci_with_owner = cmdb_stub.GetCIWithOwner(cmdb_pb2.CIIdRequest(id=incident.ci_id))

                return incident_pb2.IncidentWithCIResponse(
                incident=incident_response,
                ci_name=ci_with_owner.ci.name,
                ci_environment=ci_with_owner.ci.environment,
                owner_name=ci_with_owner.owner_name,
                owner_email=ci_with_owner.owner_email,
            )

def serve():
    setup_tracing("incident")
    start_http_server(9103)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    incident_pb2_grpc.add_IncidentServiceServicer_to_server(IncidentServiceServicer(), server)
    server.add_insecure_port("[::]:50053")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
