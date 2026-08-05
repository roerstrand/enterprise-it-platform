# ARD-0010: Async-first architecture for the Python services

## Status
Accepted

## Date
2026-08-05

## Context
The Python gRPC services (`user_server.py`, `cmdb_server.py`, `incident_server.py`) were built on the classic synchronous gRPC server model (`grpc.server(futures.ThreadPoolExecutor(max_workers=10))`), with blocking SQLAlchemy sessions and a fixed-size worker thread pool. This was the default chosen when the services were first written, without an explicit evaluation against an async alternative.

The workload these services handle is overwhelmingly I/O-bound: database queries, inter-service gRPC calls (CMDB→User, Incident→CMDB→User), Redis cache lookups, RabbitMQ event publishing, and — since the Foundry Local AI integration was added to Incident Service — an external HTTP call to a local LLM taking 18-30 seconds. A fixed thread pool ties up one of its limited worker threads for the full duration of any such call, even though the thread does no CPU work while waiting. This is a real, near-term operational risk (thread pool exhaustion under modest concurrent load), not just a theoretical concern at extreme scale.

The modern Python async ecosystem (SQLAlchemy 2.0 async engine + `asyncpg`, `grpc.aio`, `redis.asyncio`) now covers this stack's exact needs maturely, removing the historical argument that "the whole chain must be async or you gain nothing."

## Decision
All three Python gRPC services are converted to an async-first architecture:
- `grpc.aio.server()` instead of `grpc.server(futures.ThreadPoolExecutor(...))`; all servicer methods become `async def`.
- SQLAlchemy async engine (`create_async_engine`) with the `asyncpg` driver (Postgres) / `aiosqlite` (SQLite fallback), replacing the synchronous engine and session in `data/database.py`.
- Inter-service gRPC calls (CMDB→User, Incident→CMDB) use `grpc.aio.insecure_channel` with `await`.
- `caching/cache.py` uses `redis.asyncio` (same `redis` package, no new dependency).
- Genuinely blocking calls that have no async-native equivalent in this stack (bcrypt password hashing via `passlib`, RabbitMQ publish via `pika`, the Foundry Local subprocess/HTTP call) are wrapped in `asyncio.to_thread(...)` at the call site, rather than replacing their underlying libraries. This keeps the migration scoped while still not blocking the event loop.
- Alembic keeps its own separate synchronous engine (`psycopg2`) in `alembic/env.py`, independent of the app's async engine — migrations are a one-off DDL operation, not a concurrency-sensitive hot path, so sharing the async engine would add complexity for no benefit.
- Change Service (C#/.NET, ARD-0009) is unaffected — ASP.NET Core/`Grpc.AspNetCore` is already async-by-default (`Task<T>`-based).
- Existing gRPC test clients (`grpc_client.py`, `cmdb_client.py`, `incident_client.py`, `ChangeClient`) require no changes — gRPC's wire protocol is independent of the server's concurrency model; a sync client works against an async server exactly as it already does against the C# server.

## Alternatives considered
- **Keep the thread pool, just raise `max_workers`.** Rejected — raises the ceiling but doesn't remove the underlying problem (each slow I/O call still occupies a scarce, statically-sized resource), and each additional OS thread has real memory/scheduling cost.
- **Only make Incident Service async, leave CMDB/User on the thread-pool model.** Rejected — Incident Service's multi-hop calls (`GetIncidentWithCI`) depend on CMDB and User; a sync callee would block the calling coroutine's thread anyway, so the benefit only materializes if the whole call chain is async.
- **Replace `pika`/`passlib` with fully async-native libraries (`aio-pika`, an async bcrypt binding).** Deferred — `asyncio.to_thread(...)` already removes the event-loop-blocking risk without introducing new dependencies or changing connection-handling semantics; revisit only if these libraries become a measured bottleneck.

## Consequences
- Removes the thread-pool-exhaustion risk under concurrent slow I/O (e.g. multiple simultaneous incident creations while Foundry Local is generating summaries).
- `incident_server.py`'s AI-enrichment background job simplifies from `threading.Thread(...)` to `asyncio.create_task(...)`, consistent with the rest of the codebase's concurrency model instead of mixing two.
- All three Python services, all repositories, `data/database.py`, and `alembic/env.py` required changes — a full pass, not a localized fix.
- Contributors must consistently use `async def`/`await` for any new gRPC handler or repository function going forward; a stray synchronous blocking call in the handler chain would silently reintroduce the event-loop-blocking risk this ARD removes.
