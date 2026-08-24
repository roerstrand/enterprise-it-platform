# ARD-0014: RabbitMQ for CI domain events

## Status
Accepted

## Date
2026-07-25

## Context
Other parts of the platform (a future notification service, other bounded contexts) may need to react to CI lifecycle events without CMDB Service having to know about every consumer directly, or chaining synchronous gRPC calls to each of them from inside a mutation. An event-driven integration point was needed, consistent with the realistic, loosely-coupled enterprise architecture the rest of the platform demonstrates (ARD-0005, ARD-0009).

## Decision
`messaging/publisher.py` publishes CI events (currently `ci.created`) to a durable topic exchange `cmdb_events` on RabbitMQ, using `pika`'s synchronous `BlockingConnection` wrapped in `asyncio.to_thread` from the async gRPC handler in `cmdb_server.py`. Events are plain JSON, published with `delivery_mode=2` (persistent, survives a broker restart). `messaging/consumer_example.py` demonstrates the consumer side — it binds a `cmdb_events.ci_created` queue to routing key `ci.created` — but is not itself a running service; it's a reference implementation for whoever consumes these events next.

## Alternatives considered
- **Synchronous gRPC call to every interested consumer** — rejected; couples CMDB Service to knowing about every downstream consumer and blocks the CI mutation on each consumer's availability/latency.
- **`aio-pika` (native asyncio RabbitMQ client) instead of `pika` + `asyncio.to_thread`** — considered, for consistency with the rest of the async-first codebase (ARD-0010). Not adopted yet; `pika`'s `BlockingConnection` was already available and `asyncio.to_thread` is an acceptable bridge for a single short-lived publish call. Worth revisiting if publish volume grows.
- **Redis pub/sub instead of a separate broker** — rejected; no delivery guarantee. A consumer that's offline at publish time loses the event, whereas RabbitMQ's durable queues let a consumer come online later and still process the backlog.

## Consequences
- New infrastructure dependency (RabbitMQ, via `docker-compose`) alongside Postgres and Redis.
- Opens a real integration point for future services without further changes to CMDB Service — a new consumer just binds its own queue to the existing `cmdb_events` exchange.
- Only `ci.created` is published today; `UpdateCI`/`DeleteCI` don't yet publish their own events, so a consumer relying on the full CI lifecycle is incomplete until that's added.
- A blocking `pika` connection is opened per publish call rather than pooled/reused, adding per-request connection overhead — acceptable at current volume, a candidate to revisit if this becomes a bottleneck.
