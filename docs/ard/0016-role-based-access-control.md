# ARD-0016: Role-based access control (admin / operator / viewer)

## Status
Accepted

## Date
2026-08-15

## Context
JWT login (ARD-0006) only established identity — any authenticated user could call any mutating endpoint. The platform's ITSM/CMDB scope requires distinguishing who can read data from who can create/edit/delete CIs, incidents, and changes, matching how real ITSM tools gate write access by role. A decision was needed on where enforcement lives and how fine-grained the role model should be.

## Decision
Three fixed roles — `admin`, `operator`, `viewer` (`auth/security.py:ROLES`) — are embedded as a claim in the JWT issued at login (`create_access_token`). `auth/dependencies.py` exposes `get_current_user` (decodes the token; a token with no valid `role` claim is rejected outright, forcing re-login) and a `require_roles(*roles)` dependency factory. Each REST endpoint in `routers/demo.py` picks the dependency matching what it needs: plain `get_current_user` for any authenticated read, `require_roles("admin", "operator")` (aliased `manage`) for CI/incident/change mutations, `require_roles("admin")` (aliased `admin_only`) for user-role management and the audit log. Enforcement is entirely server-side in the FastAPI gateway; the gRPC layer underneath has no concept of roles at all (ARD-0005/ARD-0018 — gRPC services trust their caller). The Angular client only hides/disables actions it has no permission for — a UX convenience, not a security boundary.

## Alternatives considered
- **Enforce roles inside each gRPC service instead of the FastAPI gateway** — rejected; would mean re-implementing the same checks independently in Python and in C# (Change Service), and gRPC services have no user-identity concept today, which would require passing/verifying JWTs on every internal call.
- **Fine-grained per-action permissions** (e.g. `incident:delete`) instead of three fixed roles — rejected as unnecessary complexity for this project's scope; three roles map cleanly onto "can't touch anything", "can operate the ITSM tools", and "owns user management and audit".
- **Self-registration allowed to pick any role** — rejected; `POST /demo/api/users` always creates `viewer` (`user_server.py`), roles can only be escalated via `PUT /demo/api/users/{id}/role`, itself `admin_only` — prevents a new signup from granting itself admin.

## Consequences
- A single point of enforcement (the FastAPI gateway) for every mutating REST endpoint — easy to audit which roles can do what by reading `demo.py`.
- The gRPC services themselves remain fully open to any caller that can reach their port — acceptable because those ports are never exposed outside the internal network (nginx only proxies FastAPI), but means the security boundary is entirely perimeter-based, not defense-in-depth.
- Any new REST endpoint added later must remember to pick the right dependency (`get_current_user`/`manage`/`admin_only`) — there's no default-deny; forgetting the dependency entirely leaves the endpoint unauthenticated.
- Old JWTs issued before this change (no `role` claim) are rejected outright rather than treated as e.g. `viewer` — forces re-login for anyone with a stale token, judged safer than guessing a default role.
- **Gap identified and closed, 2026-08-24, while writing `scripts/seed_demo_data.py`:** the perimeter argument above was weaker than assumed for `user_server.py`'s `UpdateUserRole` RPC specifically. As the platform's sole privilege-escalation primitive (grants `admin` outright), it carried the same "no auth at the gRPC layer" gap as every other RPC — but for an ordinary CRUD RPC that gap is an accepted trade-off, while for a privilege-escalation RPC it was a real defense-in-depth gap. The local Docker Desktop/kubeadm cluster has no NetworkPolicy, so any caller with `kubectl` access (not just legitimate service-to-service traffic) could reach `user-server`'s ClusterIP directly and self-elevate to admin, bypassing the FastAPI gateway entirely. **Fixed:** `UpdateUserRole` now independently verifies a JWT passed as gRPC metadata (`authorization: Bearer <token>`), decoded with the same `decode_access_token` the REST layer uses, and requires `role == "admin"` in it — a second, independent enforcement point, not just the FastAPI gateway. A bootstrap exception (`any_admin_exists_from_db`) allows the call without a token only while zero admins exist in the database at all, otherwise there would be no way to ever create the first admin account. `grpc_clients/user_client.py` and `routers/demo.py` were updated to read and forward the caller's raw JWT (previously only the decoded `CurrentUser` was available at the route handler, the raw token string was discarded after decoding). A NetworkPolicy restricting which pods may reach `user-server:50051` at all remains a longer-term, separate hardening item — not needed now that the RPC enforces its own auth.
