# ARD-0017: Incident lifecycle as an explicit state machine

## Status
Accepted

## Date
2026-08-15

## Context
Incident status (`open`, `in_progress`, `resolved`, `closed`) could previously be set to any value via `UpdateIncidentStatus`/`AcceptSuggestedStatus`, with nothing preventing e.g. `open` → `closed` directly, or `resolved` → `open`. Real ITSM tools enforce a defined incident lifecycle, and the AI-suggested-status feature (`ai_suggested_status`, populated from `classify_incident_status`) needed a defined boundary for what it's even allowed to suggest and have accepted.

## Decision
`domain/incident_lifecycle.py` defines the allowed statuses and a strict, forward-only transition table (`open → in_progress → resolved → closed`; `closed` is terminal; no skipping). `validate_transition(current, new)` is called by both `UpdateIncidentStatus` and `AcceptSuggestedStatus` in `incident_server.py`; an invalid transition raises `InvalidStatusTransition`, mapped to gRPC `FAILED_PRECONDITION` and then HTTP 409 Conflict at the FastAPI gateway (distinct from 400 Bad Request, reserved for malformed input rather than a state conflict). The same module also owns severity validation (`SEVERITIES`, `validate_severity`) — a flat allow-list, not a state machine, since severity has no ordering/transition constraint.

## Alternatives considered
- **Leave status as a free-form string, validated only against an allow-list (like severity)** — rejected; would let AI-suggested-status accept nonsensical jumps (e.g. straight to `closed`), and doesn't match the ITSM tools this project models itself after.
- **Enforce the transition rule in the repository layer instead of a dedicated domain module** — rejected; keeps the business rule colocated with persistence, making it easy to bypass from a different code path. A standalone domain module makes the rule the one place both call sites (manual update, AI-accept) must go through.
- **Treat a same-status "transition" as invalid** (e.g. `open` → `open`) — rejected; `validate_transition` explicitly treats no-op transitions as a success, since the AI can legitimately suggest a status the incident is already in, and that shouldn't be an error.

## Consequences
- `AcceptSuggestedStatus` can now itself fail with 409 if the AI's suggestion is no longer valid for the incident's current state (e.g. the incident was manually closed between the suggestion being generated and being accepted) — a real race condition the caller must now handle, where previously the accept was unconditional.
- The lifecycle is fixed and linear; there's no path back from `resolved` to `in_progress` (a "reopened" incident) if that's ever needed — would require a deliberate, separate decision to extend `ALLOWED_TRANSITIONS`.
- Severity and status validation live in the same small module despite having different shapes (allow-list vs. state machine) — kept together because both are incident-domain invariants enforced at the same two call sites, not because they're conceptually the same kind of rule.
