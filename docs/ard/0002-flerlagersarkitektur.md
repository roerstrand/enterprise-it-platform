# ARD-0002: Layered architecture for endpoints

## Status
Accepted

## Date
2026-07-15

## Context
The project will grow with more resources and possibly more microservices.
A consistent pattern is needed for how a request moves through the codebase,
so that HTTP handling, business logic, and database access don't get mixed
together in the same function.

## Decision
Each resource is split into four layers, with a strict downward dependency:

```
routers/<resource>.py       (HTTP endpoints, Depends injection, status codes)
  └── services/<resource>_service.py    (business logic)
        └── repositories/<resource>_repository.py  (DB queries)
              └── data/models/<resource>_model.py   (SQLAlchemy model)
```

- Routers only know about services, never repositories or models directly.
- Services only know about repositories, never SQLAlchemy queries directly.
- Repositories are the only place that talks to the database.
- The DB session is injected via `Depends(get_db)` in the router and passed
  down as the first argument (`db: Session`) through the whole chain.

The pattern applies to all new resources going forward, not just `users`.

## Alternatives considered
- Everything in the router function (endpoint talks directly to the DB) —
  rejected, quickly becomes untestable and hard to reuse logic between HTTP and gRPC
- Generic repository/service base class — rejected for now, too few
  resources yet to justify the abstraction

## Consequences
- A new resource requires four new files (model, repository, service,
  router) — more boilerplate but clear separation of responsibilities
- Business logic in services can be reused by both the REST router and a
  future gRPC server without duplicating DB code
- Easier to test services/repositories in isolation with a mocked `db` session
