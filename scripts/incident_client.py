import grpc
import time

from protos import user_pb2, user_pb2_grpc
from protos import cmdb_pb2, cmdb_pb2_grpc
from protos import incident_pb2, incident_pb2_grpc

def run():
    with grpc.insecure_channel("localhost:50051") as user_channel:
        user_stub = user_pb2_grpc.UserServiceStub(user_channel)
        owner = user_stub.CreateUser(user_pb2.CreateUserRequest(
            name="Erik", email="erik@example.com", password="test1234"
        ))
        print(f"Created user: id={owner.id}, name={owner.name}")

    with grpc.insecure_channel("localhost:50052") as cmdb_channel:
        cmdb_stub = cmdb_pb2_grpc.CmdbServiceStub(cmdb_channel)
        ci = cmdb_stub.CreateCI(cmdb_pb2.CreateCIRequest(
            name="payment-api", ci_type="APPLICATION", environment="PROD", owner_user_id=owner.id
        ))
        print(f"Created CI: id={ci.id}, name={ci.name}, owner_user_id={owner.id}")

        with grpc.insecure_channel("localhost:50053") as incident_channel:
            incident_stub = incident_pb2_grpc.IncidentServiceStub(incident_channel)
            incident = incident_stub.CreateIncident(incident_pb2.CreateIncidentRequest(
                title="Payment API down", description="500 errors on checkout", severity="HIGH", ci_id=ci.id
            ))
            print(f"Created incident: id={incident.id}, title={incident.title}")

            enriched = incident_stub.GetIncidentWithCI(incident_pb2.IncidentIdRequest(id=incident.id))
            print("\nGetIncidentWithCI:")
            print(f"  incident={enriched.incident.title}, status={enriched.incident.status}")
            print(f"  ci_name={enriched.ci_name}, ci_environment={enriched.ci_environment}")
            print(f"  owner_name={enriched.owner_name}, owner_email={enriched.owner_email}")

            poll_interval = 2
            timeout = 60
            elapsed = 0
            fetched = incident_stub.GetIncident(incident_pb2.IncidentIdRequest(id=incident.id))
            while fetched.ai_summary_status == "pending" and elapsed < timeout:
                time.sleep(poll_interval)
                elapsed += poll_interval
                fetched = incident_stub.GetIncident(incident_pb2.IncidentIdRequest(id=incident.id))

            print(f"\nai_summary_status={fetched.ai_summary_status}, ai_summary: {fetched.ai_summary}")

if __name__ == "__main__":
    run()