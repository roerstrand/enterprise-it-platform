# ARD-0005: Removal of REST CRUD in favor of gRPC as the sole data contract

## Status
Accepted

## Date
2026-07-18

## Context
`routers/users.py` → `services/user_service.py` →
`repositories/user_repository.py` has existed since the start of the
project, as a result of the REST CRUD and the gRPC server being built as
two separate learning exercises in the same repo, without a shared
architectural line from the start. After ARD-0002 (layered architecture)
and ARD-0004 (gRPC as the only internal transport for the web demo), the
conflict became clear: the REST endpoint writes directly to the database,
entirely bypassing the gRPC contract that is meant to constitute the
service boundary.

The purpose of a microservice architecture is that data is only accessed
through a defined contract between services (here gRPC/Protobuf). A REST
endpoint that writes to the same table without going through that contract
means the boundary can be bypassed — which already caused a concrete
problem: the REST and gRPC paths needed to be updated separately for
password hashing and drifted apart before both were fixed.

## Decision
`routers/users.py` and `services/user_service.py` are removed. All
creation and reading of users happens exclusively via gRPC
(`microservices.py`), either through the web demo (`routers/demo.py`, see
ARD-0004) or the test script `grpc_client.py`.
`repositories/user_repository.py` and `data/models/user_model.py` are
kept — they are still used internally by `microservices.py`.
`schemas/user_create.py` is kept and reused for validation in the demo's
create endpoint. `schemas/user_update.py` is removed (becomes dead code,
no update path exists in the gRPC contract).

## Alternatives considered
- Keep REST but restrict it in production (e.g. bound to localhost or
  behind an environment variable) — rejected. Doesn't solve the underlying
  problem (the boundary can still be bypassed locally/during development)
  and is just complexity for a protection that already exists by removing
  the surface entirely.
- Keep REST as a pure developer tool for quick manual testing
  (curl/Swagger) — rejected. Undermines the point of the microservice
  boundary by definition, not just operationally, and the concrete
  divergence bug shows the real cost is real, not hypothetical.

## Consequences
- No REST CRUD left for `users` — `/docs` (Swagger) loses its user
  management, manual testing happens via `/demo` or `grpc_client.py` instead
- A single code path (gRPC → repository) to keep correct, instead of two
  that can drift apart
- `main.py` needs to be updated to no longer include `routers.users`
