import os

import grpc
import psycopg2

from protos import user_pb2, user_pb2_grpc
from protos import cmdb_pb2, cmdb_pb2_grpc
from protos import incident_pb2, incident_pb2_grpc

# Fallback localhost:PORT för körning lokalt via kubectl port-forward - satt till
# service-DNS-namnen (t.ex. "user-server:50051") när skriptet körs som en pod
# INNE i klustret, så seedningen slipper port-forward helt då.
USER_SERVICE_ADDR = os.getenv("USER_SERVICE_ADDR", "localhost:50051")
CMDB_SERVICE_ADDR = os.getenv("CMDB_SERVICE_ADDR", "localhost:50052")
INCIDENT_SERVICE_ADDR = os.getenv("INCIDENT_SERVICE_ADDR", "localhost:50053")

SEED_DATABASE_URL = os.getenv("SEED_DATABASE_URL", "postgresql://devuser:devpass@localhost:5433/microservices")

# Går direkt mot gRPC-servrarna, precis som cmdb_client.py/incident_client.py -
# de har ingen egen auth (JWT/RBAC enforceas bara i FastAPI-gatewayen, se demo.py),
# så det här skriptet slipper bootstrap-problemet med att behöva en admin-token
# bara för att seeda testdata.

USERS = [
    ("Admin User", "admin@test.com", "admin"),
    ("Operator User", "operator@test.com", "operator"),
    ("Viewer User", "viewer@test.com", "viewer"),
]

CIS = [
    # (name, ci_type, environment, owner index in USERS eller None)
    ("web-frontend-01", "application", "production", 0),
    ("db-02", "database", "production", 1),
    ("reporting-svc", "service", "staging", 1),
    ("auth-gateway", "application", "production", 0),
    ("cache-node-01", "cache", "production", None),
    ("batch-worker-03", "service", "staging", 1),
]

# (title, description, severity, ci index, status att sätta efteråt eller None, update-text eller None)
INCIDENTS = [
    ("Payment API returning 500 errors on checkout", "Customers report failed checkouts since 14:02 UTC, correlates with the latest deploy.", "critical", 0, "in_progress", "Rolled back the latest deploy, monitoring error rate."),
    ("Database connection pool exhausted on db-02", "Connection pool hit its max size during peak traffic, new queries are timing out.", "high", 1, "in_progress", None),
    ("Reporting dashboard slow to load for enterprise tenants", "Reports are taking 30s+ to load for tenants with large datasets.", "medium", 2, None, None),
    ("Login page CSS broken in Safari", "Layout shifts on Safari 17, buttons overlap the input fields.", "low", 0, "resolved", "Fixed a flexbox fallback issue, verified on Safari 17.4."),
    ("Auth gateway intermittent 401s after deploy", "A subset of requests get rejected with 401 right after token refresh.", "high", 3, None, None),
    ("Cache node memory usage climbing steadily", "Memory usage on cache-node-01 has grown 40% over the last 24h without a matching traffic increase.", "medium", 4, "in_progress", None),
    ("Nightly batch job failing silently", "The 02:00 batch-worker-03 job exits 0 but hasn't written output for 3 nights.", "critical", 5, None, None),
]

def reset_database():
    conn = psycopg2.connect(SEED_DATABASE_URL)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(
            'TRUNCATE incident_updates, incident_change_links, ci_relationships, '
            'incidents, configuration_items, audit_log, "Changes", users '
            'RESTART IDENTITY CASCADE;' 
        )
    conn.close()
    print("Database reset: all seed-relevant tables truncated.\n")

def run():
    reset_database()

    with grpc.insecure_channel(USER_SERVICE_ADDR) as user_channel:
        user_stub = user_pb2_grpc.UserServiceStub(user_channel)
        user_ids = []
        admin_token = None
        for name, email, role in USERS:
            user = user_stub.CreateUser(user_pb2.CreateUserRequest(name=name, email=email, password="test1234"))

            if role != "viewer":
                metadata = (("authorization", f"Bearer {admin_token}"),) if admin_token else None
                user = user_stub.UpdateUserRole(user_pb2.UpdateUserRoleRequest(id=user.id, role=role), metadata=metadata)

            if role == "admin" and admin_token is None:
                login_response = user_stub.Login(user_pb2.LoginRequest(email=email, password="test1234"))
                admin_token = login_response.access_token

            user_ids.append(user.id)
            print(f"Created user: id={user.id}, name={user.name}, role={user.role}")

    with grpc.insecure_channel(CMDB_SERVICE_ADDR) as cmdb_channel:
        cmdb_stub = cmdb_pb2_grpc.CmdbServiceStub(cmdb_channel)
        ci_ids = []
        for name, ci_type, environment, owner_idx in CIS:
            kwargs = {"name": name, "ci_type": ci_type, "environment": environment}
            if owner_idx is not None:
                kwargs["owner_user_id"] = user_ids[owner_idx]
            ci = cmdb_stub.CreateCI(cmdb_pb2.CreateCIRequest(**kwargs))
            ci_ids.append(ci.id)
            print(f"Created CI: id={ci.id}, name={ci.name}, owner_user_id={ci.owner_user_id if ci.HasField('owner_user_id') else None}")

    with grpc.insecure_channel(INCIDENT_SERVICE_ADDR) as incident_channel:
        incident_stub = incident_pb2_grpc.IncidentServiceStub(incident_channel)
        for title, description, severity, ci_idx, status, update_text in INCIDENTS:
            incident = incident_stub.CreateIncident(incident_pb2.CreateIncidentRequest(
                title=title, description=description, severity=severity, ci_id=ci_ids[ci_idx]
            ))
            print(f"Created incident: id={incident.id}, title={incident.title}, severity={incident.severity}")

            # open -> in_progress -> resolved är enda tillåtna ordningen (domain/incident_lifecycle.py) -
            # måste alltid gå via in_progress för att nå resolved, kan inte hoppa direkt dit
            if status in ("in_progress", "resolved"):
                incident_stub.UpdateIncidentStatus(incident_pb2.UpdateIncidentStatusRequest(id=incident.id, status="in_progress"))
            if status == "resolved":
                incident_stub.UpdateIncidentStatus(incident_pb2.UpdateIncidentStatusRequest(id=incident.id, status="resolved"))

            if update_text:
                incident_stub.AddIncidentUpdate(incident_pb2.AddIncidentUpdateRequest(incident_id=incident.id, text=update_text))
                print(f"  added update: {update_text}")

    print("\nSeed complete. AI summaries/suggestions are generated in the background by incident_server - "
          "give it a few seconds before checking the Angular client.")


if __name__ == "__main__":
    run()
