# ARD-0013: Redis for read-through caching in the CMDB service

## Status
Accepted

## Date
2026-07-26

## Context
CMDB reads (`GetCI`, `ListCIs`, `GetRelatedCIs`, `GetCIWithOwner`) hit Postgres on every call. CI data changes infrequently compared to how often it's read — Incident Service calls `GetCIWithOwner` on every AI summary/classification pass, and the Angular client re-lists CIs after every mutation. A decision was needed on whether to reduce this read load, and if so, how.

## Decision
Redis (`caching/cache.py`) is used as a read-through cache in `cmdb_server.py`. Each read path checks `get_cached(key)` first, falls back to Postgres on a miss, and populates the cache with `set_cached(key, value, tti_seconds=60)` (JSON-serialized, 60s default TTL). Keys are scoped per entity and per query shape (`ci:{id}`, `cis:all`, `ci_with_owner:{id}`, etc.). Mutations (`CreateCI`/`UpdateCI`/`DeleteCI`) explicitly call `delete_cached` on the relevant keys rather than relying on TTL expiry alone, so an edit is visible immediately rather than up to 60s later.

## Alternatives considered
- **In-process cache (e.g. `functools.lru_cache`)** — rejected; doesn't work across multiple replicas of `cmdb_server` (ARD-0011 runs this on Kubernetes with replica scaling), and can't be invalidated from a different process when a mutation happens.
- **No caching** — rejected; CMDB is looked up repeatedly per request by Incident Service's AI enrichment and by every CI list view, each hitting Postgres directly.
- **Longer TTL, no explicit invalidation** — rejected; would let a CI edit remain invisible in the same request cycle (edit CI → refresh list) for up to the TTL, which isn't acceptable UX.

## Consequences
- CI reads are fast after the first fetch, but every read path now has an extra failure mode: unlike the write-path invalidation (ARD-0015), the read-path `get_cached`/`set_cached` calls are **not** wrapped in `try/except` — a Redis outage currently breaks CI reads instead of falling back to the database.
- Cache invalidation keys are kept in sync by hand at every mutation site; a future mutation that forgets to invalidate the right key(s) will silently serve stale data for up to 60s.
- Adds Redis as required local infrastructure (`docker-compose`) and a new external dependency for the CMDB service.
