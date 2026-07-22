# ARD-0007: CMDB Service — Configuration Item model and gRPC contract (V1)

## Status
Proposed

## Date
2026-07-22

## Context
The platform is evolving from a single Identity-focused app into an
enterprise IT operations platform (see project vision, 2026-07-22
decision). The CMDB is the core of that platform: it must represent
heterogeneous object types (servers, applications, APIs, databases,
business systems) and the relationships between them (runs on, depends
on, used by, part of), so that future ITSM modules (Incident, Change,
Asset) can query "what is affected" starting from a single object.

A decision is needed on how to model object types and relationships
without hard-coding a new database table for every object type the
platform will ever need, and on how the CMDB Service fits the existing
gRPC-only, layered architecture (ARD-0002, ARD-0005).

## Decision
- **Generic Configuration Item (CI) model, not one table per object
  type.** A single `configuration_items` table holds all CI types
  (`SERVER`, `APPLICATION`, `API`, `DATABASE`, `BUSINESS_SYSTEM`, ...),
  distinguished by a `ci_type` column, plus `name` and `environment`
  (`DEV`/`TEST`/`PROD`). Adding a new CI type is a new enum value, not a
  new table/migration.
- **Generic relationship model.** A single `ci_relationships` table
  holds directed edges between two CIs (`source_ci_id`, `target_ci_id`,
  `relationship_type`: `RUNS_ON`, `DEPENDS_ON`, `USES`, `PART_OF`). This
  is what lets "an application runs on a server" and "a business system
  consists of several services" be expressed with the same table.
- **`Team` stays a separate, lightweight table** (id, name), referenced
  from a CI via `owner_team_id`, not modeled as a CI itself. Keeps V1
  scope tight; promoting Team to a full CI type is a possible future
  ARD if ownership needs to participate in relationship queries too.
- **CMDB Service is a new, separate gRPC server process** (`cmdb_service.py`,
  own port, e.g. `50052`), with its own contract (`protos/cmdb.proto`)
  and its own layered stack (`repositories/cmdb_repository.py`,
  `data/models/ci_model.py`, `data/models/relationship_model.py`),
  mirroring the existing Identity service structure rather than being
  bolted onto `microservices.py`.
- **Shares the existing Postgres instance** (same `docker-compose.yml`,
  same `data/database.py` engine/`SessionLocal`/`get_db_context`) rather
  than a separate database. Consistent with the ARD-0004 simplification
  already accepted for this monorepo; revisit when/if the platform
  actually deploys services independently (Kubernetes phase).
- V1 gRPC contract (minimum to prove the model): `CreateCI`, `GetCI`,
  `ListCIs`, `CreateRelationship`, `GetRelatedCIs` (returns CIs directly
  connected to a given CI — the query later ITSM modules will need).

## Alternatives considered
- **One table per CI type** (`servers`, `applications`, `databases`, ...)
  — rejected. Matches how the vision doc lists CI types, but every new
  type becomes a schema migration, and cross-type relationship queries
  ("what depends on this database") need N different join paths instead
  of one. Real CMDB products (ServiceNow's `cmdb_ci` base table) use the
  generic-CI approach for exactly this reason.
- **Graph database (e.g. Neo4j) for CI relationships** — rejected for
  V1. Relationship queries are genuinely graph-shaped, but introducing a
  second datastore this early adds operational complexity before the
  relational model has even been proven insufficient. Worth revisiting
  once relationship-traversal queries (multi-hop impact analysis) become
  a real bottleneck.
- **Bolt CMDB endpoints onto the existing `microservices.py`/`UserService`**
  — rejected. Defeats the point of the roadmap (demonstrating an actual
  microservice architecture with independent services); Identity and
  CMDB are different bounded contexts and should be able to evolve/scale
  independently.
- **REST between CMDB and future consumer services (Incident, Change)**
  — rejected, per the 2026-07-22 decision that gRPC remains the sole
  internal transport (ARD-0005 stands).

## Consequences
- New proto file, new generated pb2 files, new server process to run
  alongside `microservices.py` — local dev now means three processes
  (`uvicorn`, `microservices.py`, `cmdb_service.py`) instead of two.
- `ci_type` and `relationship_type` as string/enum columns mean the
  database itself won't stop an invalid combination (e.g. a `DATABASE`
  CI with a `RUNS_ON` target that's also a `DATABASE`) — validation of
  "sensible" relationships happens in the service layer, not the schema,
  at least for V1.
- Querying "everything affected by this server" is a small number of
  joins for V1 (direct relationships only, via `GetRelatedCIs`).
  Multi-hop impact analysis (what's indirectly affected) is explicitly
  out of scope for V1 and will need its own design pass once Incident
  Service consumes this.
- The existing frontend demo can optionally get a minimal CI list view
  later; not required for this ARD to be accepted, since the vision
  explicitly keeps frontend work secondary to backend/architecture.
