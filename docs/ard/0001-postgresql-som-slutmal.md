# ARD-0001: PostgreSQL as the final database

## Status
Proposed

## Date
2026-07-15

## Context
The project currently uses SQLite for development. SQLite is simple to get
started with but lacks e.g. good support for concurrent writes, lacks real
data types for some fields, and is not suitable for production in a
microservice environment.

## Decision
The project moves toward PostgreSQL as the production database. SQLite is
kept for now as the local development/test database.

## Alternatives considered
- Keep SQLite in production — rejected due to poor concurrency and scalability
- MySQL — rejected, PostgreSQL has better support for JSON fields and stricter typing

## Consequences
- The SQLAlchemy models must be database-agnostic (avoid SQLite-specific types)
- A migration strategy (e.g. Alembic) is needed before the switch happens
- The connection string in database.py must become environment-dependent (dev=SQLite, prod=PostgreSQL)
