# enterprise-it-platform

FastAPI-based microservice demo with gRPC as the internal data contract and PostgreSQL as the database.

## Architecture

See `docs/ard/` for all architecture decisions (ARDs). Summary:

- Layered architecture: router → service → repository → model (ARD-0002)
- PostgreSQL as the production database, run locally via Docker Compose (ARD-0001, ARD-0003)
- All data access happens via gRPC, no REST CRUD (ARD-0005)
- Web demo at `/demo` talks gRPC to `grpc_servers/user_server.py`, with a strict CSP (ARD-0004)
- JWT login via gRPC (ARD-0006)
- CMDB Service (`grpc_servers/cmdb_server.py`) manages Configuration Items over gRPC (ARD-0007)
- Incident Service (`grpc_servers/incident_server.py`) manages incidents over gRPC, enriches with CI/owner data from the CMDB service
- Change Service is implemented in C#/.NET — the platform's first polyglot service (ARD-0009)
- Audit Service (`grpc_servers/audit_server.py`) is an append-only event log shared by every mutating service (Python and C#), queried read-only by Admins via `/demo/api/audit` (ARD-0018)
- JWT auth with roles (admin/operator/viewer) is enforced server-side per endpoint (ARD-0016); the Angular client only hides/disables actions it has no permission for
- Incident status follows a strict forward-only lifecycle (open → in_progress → resolved → closed, ARD-0017)
- Observability via Prometheus + Grafana: FastAPI exposes `/metrics`, each gRPC server exposes its own metrics port (ARD-0008)
- nginx reverse-proxies port 80 to the FastAPI app on port 8000; gRPC between services stays internal, never exposed through nginx
- Redis used for read-through caching in the CMDB service (ARD-0013); RabbitMQ publishes CI domain events (ARD-0014); both are best-effort — a broker/cache outage never fails a mutation whose database write already succeeded (ARD-0015)
- Azure infrastructure (resource group, Container Registry, secretless OIDC identity for GitHub Actions) is provisioned via Terraform, the first step of an AKS migration (ARD-0019)

## Architecture Decision Records (ARD)

Architecture decisions are documented as ARDs in `docs/ard/`, one per decision, numbered `000X-title.md`. Template: `docs/ard/0001-template.md`.

| ARD | Title | Status |
|-----|-------|--------|
| [0001](docs/ard/0001-postgresql-som-slutmal.md) | PostgreSQL as the final database | Proposed |
| [0002](docs/ard/0002-flerlagersarkitektur.md) | Layered architecture for endpoints | Accepted |
| [0003](docs/ard/0003-docker-compose-for-lokal-postgres.md) | Docker Compose for local PostgreSQL development | Accepted |
| [0004](docs/ard/0004-webbdemo-grpc-och-csp.md) | Web demo client with gRPC and strict CSP | Accepted |
| [0005](docs/ard/0005-ta-bort-rest-crud-endast-grpc.md) | Removal of REST CRUD in favor of gRPC | Accepted |
| [0006](docs/ard/0006-jwt-inloggning.md) | JWT login via gRPC | Accepted |
| [0007](docs/ard/0007-cmdb-service-configuration-items.md) | CMDB Service — Configuration Item model and gRPC contract (V1) | Accepted |
| [0008](docs/ard/0008-observability-prometheus-grafana-opentelemetry.md) | Observability — Prometheus, Grafana, OpenTelemetry (V1) | Proposed |
| [0009](docs/ard/0009-change-service-csharp-dotnet.md) | Change Service implemented in C#/.NET (first polyglot microservice) | Proposed |
| [0010](docs/ard/0010-async-first-python-services.md) | Async-first Python services | Accepted |
| [0011](docs/ard/0011-kubernetes-local-orchestration.md) | Kubernetes for local orchestration | Accepted |
| [0012](docs/ard/0012-uv-python-dependency-management.md) | uv for Python dependency management | Accepted |
| [0013](docs/ard/0013-redis-caching-cmdb.md) | Redis for read-through caching in the CMDB service | Accepted |
| [0014](docs/ard/0014-rabbitmq-ci-domain-events.md) | RabbitMQ for CI domain events | Accepted |
| [0015](docs/ard/0015-graceful-degradation-broker-cache-outages.md) | Graceful degradation when the broker or cache is unavailable | Accepted |
| [0016](docs/ard/0016-role-based-access-control.md) | Role-based access control (admin / operator / viewer) | Accepted |
| [0017](docs/ard/0017-incident-lifecycle-state-machine.md) | Incident lifecycle as an explicit state machine | Accepted |
| [0018](docs/ard/0018-audit-service.md) | Audit Service — append-only event log shared across Python and C# | Accepted |
| [0019](docs/ard/0019-terraform-azure-infrastructure.md) | Terraform-provisioned Azure infrastructure (start of the AKS migration) | Proposed |

New decision: copy the template, number it next in sequence, fill it in.

## Running locally

The Python backend lives in `server/` — steps 3, 4, 5 and 7 are run with `server/` as the working directory.

1. `docker compose up -d` — starts infrastructure: PostgreSQL (5433), Redis, RabbitMQ, Prometheus, Grafana, Jaeger, and nginx (port 80, proxies to FastAPI on 8000)
2. A `.env` with `DATABASE_URL` must exist at the repo root (git-ignored, see ARD-0003)
3. `cd server && python -m grpc_servers.user_server` — Identity/User gRPC server (port 50051)
4. `cd server && python -m grpc_servers.cmdb_server` — CMDB gRPC server (port 50052)
5. `cd server && python -m grpc_servers.incident_server` — Incident gRPC server (port 50053)
6. `dotnet run --project server/ChangeService` — Change Service, C#/.NET gRPC server (port 50054, ARD-0009)
7. `cd server && python -m grpc_servers.audit_server` — Audit gRPC server (port 50055)
8. `cd server && uvicorn main:app --reload` — starts FastAPI, web demo at `/demo` (port 8000)
9. `cd angular-client && ng serve` — Angular client (port 4200)
