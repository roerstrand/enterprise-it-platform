# ARD-0008: Observability — Prometheus, Grafana, OpenTelemetry (V1)

## Status
Proposed

## Date
2026-07-23

## Context
The platform now runs three separate processes locally (`uvicorn`, the
Identity gRPC server `user_server.py`, the CMDB gRPC server
`cmdb_server.py`), each talking to a shared Postgres instance. A failure or
slowdown in one process can surface as a symptom in another — e.g. `/demo`
timing out because `cmdb_server.py` is down produces no useful signal in
`uvicorn`'s own logs. Per the platform vision (2026-07-22), observability is
the next roadmap priority after the CMDB core, and is meant to become part
of the platform itself rather than a standalone demo.

A decision is needed on what gets instrumented first, how metrics are
exposed by processes that are not HTTP servers (the two gRPC services), and
how Prometheus/Grafana are run alongside the existing Postgres container.

## Decision
- **Metrics first, tracing second.** V1 scope is Prometheus + Grafana only.
  OpenTelemetry-based distributed tracing is deferred to a later ARD, once
  there are enough services and cross-service call chains (e.g. once an
  Incident Service calls the CMDB Service) for a trace to actually show
  something a single log can't. Introducing tracing before that point adds
  instrumentation overhead without a payoff.
- **`uvicorn`/FastAPI (`main.py`)** gets a `/metrics` endpoint via
  `prometheus-fastapi-instrumentator`, exposed on the same port (8000) the
  app already serves on. This covers HTTP request counts, latencies, and
  status codes for the web demo automatically.
- **gRPC servers expose metrics on a separate plain HTTP port**, since gRPC
  itself doesn't serve HTTP. Each gRPC server process starts a
  `prometheus_client.start_http_server(...)` alongside its gRPC server:
  - `user_server.py` — gRPC on `50051`, metrics on `9101`
  - `cmdb_server.py` — gRPC on `50052`, metrics on `9102`
  V1 metrics per gRPC method: call count and latency, using a
  `prometheus_client.Histogram` wrapping each servicer method (or a small
  decorator shared by both servicers, to avoid repeating the same
  instrumentation code per method).
- **Prometheus and Grafana run as two new services in the existing
  `docker-compose.yml`**, alongside Postgres. Prometheus is configured
  (`prometheus.yml`, new file) to scrape `host.docker.internal:8000/metrics`,
  `:9101/metrics`, `:9102/metrics` — the app processes keep running natively
  on the host (not containerized) exactly as they do today, consistent with
  ARD-0003's approach of only containerizing infrastructure, not app code,
  for local dev. Grafana connects to Prometheus as its datasource.

## Alternatives considered
- **Push-based metrics (e.g. StatsD) instead of Prometheus's pull model** —
  rejected. Pull/scrape is the standard pattern in Kubernetes-native
  environments (Prometheus is a CNCF project, same lineage as Kubernetes,
  which is later on the roadmap) — learning the pull model now is directly
  transferable.
- **Managed/vendor observability (e.g. Datadog, Grafana Cloud) instead of
  self-hosted** — rejected for V1. A managed vendor hides exactly the
  mechanics (scrape config, exporters, dashboard-as-code) this project
  exists to learn, and adds an external account/cost dependency to a local
  learning setup.
- **OpenTelemetry Collector + tracing from the start, metrics included** —
  rejected for V1, see Decision above. Revisit once multi-service call
  chains exist to trace.
- **Instrumenting via `main.py` importing gRPC servers' internals to expose
  one combined `/metrics` endpoint** — rejected. Keeps each service
  self-contained and independently scrapable, consistent with each service
  owning its own process boundary (ARD-0004, ARD-0007).

## Consequences
- Local dev now means running two extra containers (Prometheus, Grafana) in
  addition to Postgres, still via a single `docker compose up -d`.
- New dependency: `prometheus-client` (gRPC servers) and
  `prometheus-fastapi-instrumentator` (FastAPI). No code changes to
  business logic — instrumentation wraps existing servicer methods and the
  FastAPI app.
- `docker-compose.yml` needs a new `prometheus.yml` scrape-config file
  checked into the repo, and Grafana dashboards will initially be built
  manually in the UI — dashboard-as-code (provisioning via files) is a
  reasonable follow-up once the first dashboard proves useful, not required
  for V1.
- Every future service (Asset, Incident, Discovery, ...) is expected to
  follow the same pattern: HTTP services get `/metrics` via the
  instrumentator, gRPC services start a `prometheus_client` HTTP server on
  their own metrics port. Worth stating as a convention here so it doesn't
  need re-deciding per service.
