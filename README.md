# python_microservices

FastAPI-based microservice demo with gRPC as the internal data contract and PostgreSQL as the database.

## Architecture

See `docs/ard/` for all architecture decisions (ARDs). Summary:

- Layered architecture: router → service → repository → model (ARD-0002)
- PostgreSQL as the production database, run locally via Docker Compose (ARD-0001, ARD-0003)
- All data access happens via gRPC, no REST CRUD (ARD-0005)
- Web demo at `/demo` talks gRPC to `microservices.py`, with a strict CSP (ARD-0004)

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
| [0007](docs/ard/0007-cmdb-service-configuration-items.md) | CMDB Service — Configuration Item model and gRPC contract (V1) | Proposed |

New decision: copy the template, number it next in sequence, fill it in.

## Running locally

1. `docker compose up -d` — starts PostgreSQL on port 5433
2. A `.env` with `DATABASE_URL` must exist (git-ignored, see ARD-0003)
3. `python microservices.py` — starts the gRPC server
4. `uvicorn main:app --reload` — starts FastAPI, web demo at `/demo`
