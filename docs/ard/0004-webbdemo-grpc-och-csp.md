# ARD-0004: Web demo client with gRPC as internal transport and strict CSP

## Status
Accepted

## Date
2026-07-16

## Context
A way is needed to show that the system works without opening Swagger, and
to demonstrate internal gRPC communication between the FastAPI process and
the existing microservice (`user_server.py`). The project's principle is
that internal communication happens via gRPC/Protobuf, never REST-to-REST.

## Decision
- FastAPI (`main.py`) serves a static HTML/CSS/JS client under `/demo`.
- The client's endpoints (`routers/demo.py`) talk gRPC to the existing
  microservice instead of going through `repository` directly — a
  dedicated gRPC client module (`grpc_clients/user_client.py`) reuses the
  same channel/stub pattern already present in `grpc_client.py`.
- `user_server.py` keeps running as a separate process (started on its
  own, alongside `uvicorn main:app`), since it's exactly two separate
  processes talking to each other that makes the demo a genuine
  microservice demonstration.
- Security headers and Content-Security-Policy are handled in a dedicated
  middleware (`middleware/security_headers.py`), not scattered across routers.
- HTML/CSS/JS is structured without inline code, so a strict CSP
  (`script-src 'self'`, `style-src 'self'`, no `unsafe-inline`) works
  without exceptions.

## Alternatives considered
- Demo endpoints going directly against `repository` — rejected, doesn't
  demonstrate the gRPC flow and contradicts the project's purpose
- Inline JS/CSS for simplicity — rejected, makes a strict CSP impossible
- Full isolation with separate database/repository code per service —
  rejected for this project, see consequence below

## Consequences
- Requires `user_server.py` to run as a separate process for `/demo` to
  work — a reasonable error must be handled in the UI if that process is down
  (the gRPC call fails)
- `main.py` (FastAPI) and `user_server.py` (gRPC) still share the same
  `repositories/` code and the same database. This is a deliberate
  simplification for a learning project in a monorepo — a "pure"
  microservice architecture would have each service own its own database
  access and only share a contract (the proto file), not Python modules.
  Building that out now would be a separate, larger decision and is not
  part of this feature.
