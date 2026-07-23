import grpc
from concurrent import futures
from prometheus_client import start_http_server

from protos import cmdb_pb2
from protos import cmdb_pb2_grpc

from repositories.cmdb_repository import (
    create_ci_in_db,
    get_ci_by_id_from_db,
    get_all_cis_from_db,
    create_relationship_in_db,
    get_related_cis_from_db,
)

from data.database import get_db_context
from observability.grpc_metrics import track_grpc_metrics

def _to_ci_response(ci):
    response = cmdb_pb2.CIResponse(
        id=ci.id, name=ci.name, ci_type=ci.ci_type, environment=ci.environment
    )
    if ci.owner_team_id is not None:
        response.owner_team_id = ci.owner_team_id
    return response

class CmdbServiceServicer(cmdb_pb2_grpc.CmdbServiceServicer):

    @track_grpc_metrics("cmdb")
    def CreateCI(self, request, context):
        with get_db_context() as db:
            owner_team_id = request.owner_team_id if request.HasField("owner_team_id") else None
            ci = create_ci_in_db(db, request.name, request.ci_type, request.enviroment, owner_team_id)
            return _to_ci_response(ci)

    @track_grpc_metrics("cmdb")
    def GetCI(self, request, context):
        with get_db_context() as db:
            ci = get_ci_by_id_from_db(db, request.id)
            if ci:
                return _to_ci_response(ci)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("CI {request.id} not found")
            return cmdb_pb2.CIResponse()

    @track_grpc_metrics("cmdb")
    def ListCIs(self, request, context):
        with get_db_context() as db:
            cis = get_all_cis_from_db(db)
            return cmdb_pb2.CIList(cis=[_to_ci_response(ci) for ci in cis])

    @track_grpc_metrics("cmdb")
    def CreateRelationship(self, request, context):
        with get_db_context() as db:
            relationship = create_relationship_in_db(
                db, request.source_ci_id, request.target_ci_id, request.relationship_type
            )
            return cmdb_pb2.RelationshipResponse(
                id=relationship.id,
                source_ci_id=relationship.source_ci_id,
                target_ci_id=relationship.target_ci_id,
                relationship_type=relationship.relationship_type,
            )

    @track_grpc_metrics("cmdb")
    def GetRelatedCIs(self, request, context):
        with get_db_context() as db:
            cis = get_related_cis_from_db(db, request.id)
            return cmdb_pb2.CIList(cis=[_to_ci_response(ci) for ci in cis])

def serve():
    start_http_server(9102)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cmdb_pb2_grpc.add_CmdbServiceServicer_to_server(CmdbServiceServicer(), server)
    server.add_insecure_port("[::]:50052")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()


    