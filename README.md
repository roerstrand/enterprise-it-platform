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
- Observability via Prometheus + Grafana: FastAPI exposes `/metrics`, each gRPC server exposes its own metrics port (ARD-0008)
- nginx reverse-proxies port 80 to the FastAPI app on port 8000; gRPC between services stays internal, never exposed through nginx
- Redis used for caching (`caching/cache.py`)

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

New decision: copy the template, number it next in sequence, fill it in.

## Running locally

1. `docker compose up -d` — starts infrastructure: PostgreSQL (5433), Redis, RabbitMQ, Prometheus, Grafana, Jaeger, and nginx (port 80, proxies to FastAPI on 8000)
2. A `.env` with `DATABASE_URL` must exist (git-ignored, see ARD-0003)
3. `python -m grpc_servers.user_server` — Identity/User gRPC server (port 50051)
4. `python -m grpc_servers.cmdb_server` — CMDB gRPC server (port 50052)
5. `python -m grpc_servers.incident_server` — Incident gRPC server (port 50053)
6. `dotnet run --project ChangeService` — Change Service, C#/.NET gRPC server (port 50054, ARD-0009)
7. `uvicorn main:app --reload` — starts FastAPI, web demo at `/demo` (port 8000)
