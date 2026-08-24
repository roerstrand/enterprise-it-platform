# ARD-0018: Audit Service — append-only event log shared across Python and C#

## Status
Accepted

## Date
2026-08-15

## Context
RBAC (ARD-0016) determines who is *allowed* to perform an action, but not what actually *happened* — there was no record of who created, edited, or deleted which CI/incident/change, or when a status/severity was overridden. This becomes a hard requirement once role separation exists (an Admin needs to be able to answer "who deleted this CI"), and the platform's polyglot direction (ARD-0009) meant the answer needed to work identically for the Python services and the C# Change Service.

## Decision
A new gRPC microservice, Audit Service (`grpc_servers/audit_server.py`, port 50055), owns a single `audit_log` table (`AuditLogModel`) that no repository function ever updates or deletes — genuinely append-only. `protos/audit.proto` defines `RecordAuditEvent`/`ListAuditEvents`; every other service (CMDB, Incident, and the C# Change Service, via the same generated `Audit.cs`/`AuditGrpc.cs` stubs) calls `RecordAuditEvent` after a successful mutation, passing actor identity, an action name, entity type/id, and a JSON `before`/`after` snapshot. `record_audit_event` (`grpc_clients/audit_client.py`) is deliberately best-effort: a `grpc.RpcError` is caught and logged, never raised — the same "the database write is the source of truth" principle as ARD-0015, applied to a third piece of optional infrastructure. Reads (`ListAuditEvents`, exposed as `GET /demo/api/audit`) are gated `admin_only` (ARD-0016).

## Alternatives considered
- **Each service writes its own audit rows to its own database** — rejected; would fragment the audit trail across three databases/languages, making a single "who did what, when" view impossible without a separate aggregation step.
- **Log audit events to structured stdout only** (already collected via the existing observability stack, ARD-0008) — rejected; logs aren't queryable by entity or reliably retained/indexed the way an admin-facing "history for this incident" view needs.
- **Make audit recording synchronous/required** (fail the mutation if audit recording fails) — rejected, for the same reason as ARD-0015; an audit-trail gap is preferable to a false-negative failure on a mutation that actually succeeded.

## Consequences
- A second proof point (after Change Service, ARD-0009) that gRPC contracts in this platform are language-agnostic — the same `audit.proto` compiles to both Python stubs and C# stubs (`Audit.cs`/`AuditGrpc.cs`), and both call the identical service.
- Every mutating call site across three services now makes an extra outbound gRPC call on its success path; kept off the critical path for correctness (best-effort, per above) but still adds latency before the response returns.
- Because recording is best-effort, the audit log is not a guaranteed-complete record — an Audit Service outage during a burst of mutations silently loses those entries rather than queuing/retrying them.
- `before_json`/`after_json` are stored as plain JSON strings rather than a native JSON/JSONB column, specifically to stay portable between local SQLite-style dev and Postgres (see the model's own comment) — trades native JSON querying for portability.
