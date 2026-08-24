# ARD-0015: Graceful degradation when the broker or cache is unavailable

## Status
Accepted

## Date
2026-08-14

## Context
`CreateCI`/`UpdateCI`/`DeleteCI` originally called `publish_event` (ARD-0014) and `delete_cached` (ARD-0013) inline and unguarded. When RabbitMQ or Redis was unreachable, the exception propagated out of the gRPC handler and the entire mutation failed — even though the underlying Postgres write (`create_ci_in_db`/`update_ci_in_db`/`delete_ci_from_db`) had already committed. The client would see an error for a mutation that had, in fact, succeeded: the database and the client's view of reality disagreed.

## Decision
The publish and cache-invalidation calls on the CI mutation paths are each wrapped in their own `try/except Exception`, logged to stdout, and swallowed. The database write is the source of truth and alone determines the response returned to the client; RabbitMQ/Redis are treated as best-effort side effects of a successful mutation, not preconditions for it. The same principle already applies to the AI enrichment calls in `incident_server.py` and to `audit_client.record_audit_event` (ARD-0018) — broker, cache, and audit-service outages must never fail a business mutation whose database write already succeeded.

## Alternatives considered
- **Let the mutation fail if publish/cache-invalidation fails (original behavior)** — rejected; makes the availability of secondary infrastructure a hard dependency for a database write to be considered successful, and produces false-negative errors for the client.
- **Outbox pattern** (write the event to the same DB transaction, a separate process relays it to RabbitMQ) — the theoretically correct fix for guaranteed delivery. Not implemented; today a publish failure means the event is simply lost, not retried. Deferred as over-engineering for this project's current scale — noted here as the natural next step if event-delivery guarantees become a real requirement.
- **Circuit breaker around the broker/cache clients** — rejected for now, same reasoning; a bare `try/except` is sufficient at current load, and a circuit breaker adds meaningful complexity (state tracking, half-open probing) for a benefit that isn't needed yet.

## Consequences
- CI mutations are now resilient to RabbitMQ/Redis outages — the write succeeds and the client gets a correct response regardless.
- Swallowed failures are only visible via stdout logs (`print(...)`) — there is no metric or alert today if publishing/cache-invalidation is failing continuously; an operator would only notice via stale cache reads or a missing downstream event stream.
- This pattern is only applied on the CI mutation paths (`cmdb_server.py`) and the specific call sites named above — it hasn't been applied uniformly. The CI **read** paths' `get_cached`/`set_cached` calls (`GetCI`, `ListCIs`, etc.) are still unguarded — see ARD-0013's consequences.
- Because failures are swallowed rather than retried, an event lost to a RabbitMQ outage is lost permanently (no outbox/retry), and the cache can keep serving stale data for up to its TTL if an invalidation call failed silently.
