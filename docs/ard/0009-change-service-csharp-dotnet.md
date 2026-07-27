# ARD-0009: Change Service implemented in C#/.NET (first polyglot microservice)

## Status
Proposed

## Date
2026-07-27

## Context
All microservices in the platform are currently implemented in Python (FastAPI for REST, grpc for internal RPC). The platform's long-term direction calls for a deliberately polyglot architecture, to demonstrate a realistic enterprise setup where different services are owned by different teams using different stacks. Change Management (approval workflow) is the next ITSM module on the roadmap, following Incident Management. A decision is needed on whether to add it in Python for consistency, or introduce a new language/runtime.

## Decision
The Change Service is implemented in C#/.NET using ASP.NET Core with `Grpc.AspNetCore`. It exposes a gRPC contract only, consistent with the platform's established internal transport (ARD-0005 — gRPC is the sole inter-service protocol). It connects to the same shared Postgres instance as the other services, using a separate `changes` table. References to other domains (e.g. a change referencing a Configuration Item) are resolved via gRPC calls to the owning service, not shared-database foreign keys — the same pattern already used by Incident Service toward CMDB Service.

## Alternatives considered
- **Node.js/Express + grpc-js** — also planned as a future polyglot addition, but only one new language is introduced at a time; deferred to a later service.
- **Python, for consistency with the rest of the platform** — rejected; the roadmap explicitly calls for demonstrating a realistic polyglot enterprise environment, which requires at least one non-Python service.
- **REST instead of gRPC for this service** — rejected; would reintroduce a transport ARD-0005 already closed, without a new justification for superseding it.

## Consequences
- Demonstrates a working polyglot setup: a Python service and a C# service interoperating over the same gRPC contracts, with no shared code between the two runtimes.
- Strengthens portfolio relevance for roles that touch .NET/enterprise stacks alongside Python.
- Adds a second build/runtime toolchain (.NET SDK, NuGet) to the project, alongside the existing Python venv workflow.
- Cross-cutting concerns already solved once in Python (Prometheus metrics, OpenTelemetry tracing, structured logging) need a separate, equivalent implementation in .NET rather than being reused directly.
