import grpc
from protos import cmdb_pb2
from protos import cmdb_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50052") as channel:
        stub = cmdb_pb2_grpc.CmdbServiceStub(channel)

        server_ci = stub.CreateCI(cmdb_pb2.CreateCIRequest(
            name="web-01", ci_type="SERVER", environment="PROD"
        ))
        print(f"Created CI: id={server_ci.id}, name={server_ci.name}, type={server_ci.ci_type}")

        app_ci = stub.CreateCI(cmdb_pb2.CreateCIRequest(
            name="checkout-app", ci_type="APPLICATION", environment="PROD"
        ))
        print(f"Created CI: id={app_ci.id}, name={app_ci.name}, type={app_ci.ci_type}")

        stub.CreateRelationship(cmdb_pb2.CreateRelationshipRequest(
            source_ci_id=app_ci.id, target_ci_id=server_ci.id, relationship_type="RUNS_ON"
        ))
        print(f"\nRelationship created: {app_ci.name} RUNS_ON {server_ci.name}")

        all_cis = stub.ListCIs(cmdb_pb2.Empty())
        print("\nAll CIs:")
        for ci in all_cis.cis:
            print(f" id={ci.id}, name={ci.name}, type={ci.ci_type}")

        related = stub.GetRelatCIs(cmdb_pb2.CIIdRequest(id=app_ci.id))
        print(f"\nCIs related to {app_ci.name}:")
        for ci in related.cis:
            print(f" id={ci.id}, name={ci.name}")

if __name__ == "__main__":
    run()