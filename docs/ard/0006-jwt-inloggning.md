# ARD-0006: JWT login via gRPC

## Status
Proposed

## Date
2026-07-21

## Context
Password hashing exists (`auth/security.py`, `create_access_token`) but no
login endpoint or protected route exists yet. Per ARD-0005, all user data
access goes through gRPC — a login endpoint must follow the same contract
rather than bypassing it as a REST-only shortcut.

## Decision
- `protos/user.proto` gets a `Login(LoginRequest) returns (TokenResponse)`
  RPC. `LoginRequest` carries `email`/`password`; `TokenResponse` carries
  `access_token`/`token_type`.
- `UserServiceServicer.Login` in `microservices.py` verifies the password
  with `verify_password` and returns a token from `create_access_token`.
- `routers/demo.py` exposes `POST /demo/api/login`, which calls the gRPC
  `Login` RPC via `grpc_clients/user_client.py`, mirroring the existing
  `create_user` pattern from ARD-0004.
- A `get_current_user` dependency (`auth/security.py` or new
  `auth/dependencies.py`) decodes the JWT from the `Authorization` header
  for protected routes.

## Alternatives considered
- REST-only login endpoint bypassing gRPC — rejected, repeats the ARD-0005
  problem of a second code path around the service boundary.
- Session cookies instead of JWT — rejected, `create_access_token` already
  exists and is JWT-based; switching strategy is a separate decision.

## Consequences
- `user_pb2`/`user_pb2_grpc` must be regenerated after the proto change
  (remember the manual import fix on line 6 of `user_pb2_grpc.py`, see
  project memory).
- Protected demo routes need a way to carry the token from the browser
  (e.g. stored client-side, sent as `Authorization: Bearer <token>`).
