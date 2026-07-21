# ARD-0003: Docker Compose for local PostgreSQL development

## Status
Accepted

## Date
2026-07-16

## Context
After ARD-0001 (PostgreSQL as the final target), a reproducible way to run
a local Postgres instance for development is needed, without manually
specifying `docker run` flags on every startup. The machine also has a
native Windows PostgreSQL service already listening on port 5432, which
conflicts with a Docker container on the same port and produces a masked
`UnicodeDecodeError` in psycopg2 instead of a clear authentication error.

## Decision
- `docker-compose.yml` in the project root defines the Postgres container
  (`postgres:16`, named volume for persistence, host port 5433 mapped to
  container port 5432 to avoid conflicting with the native service).
- A `.env` file (git-ignored) holds `DATABASE_URL`, loaded via
  `python-dotenv` (`load_dotenv()`) at the top of `data/database.py` before
  `os.getenv("DATABASE_URL", ...)` is read.
- The container is started/stopped with `docker compose up -d` /
  `docker compose down` instead of individual `docker run` commands.

## Alternatives considered
- Manual `docker run` command on every startup — rejected, hard to
  remember flags and risk of mapping the wrong port again
- `.env` only, without docker-compose — rejected, doesn't solve the
  container's configuration, only the connection string

## Consequences
- A new developer can run `docker compose up -d` and get the correct
  database without knowing about the port conflict in advance
- `load_dotenv()` does not override an already-set environment variable in
  the session — if `$env:DATABASE_URL` was set manually with the wrong
  port earlier in the same session, it wins over `.env` until it's cleared
  (`Remove-Item Env:\DATABASE_URL`)
- One extra file (`docker-compose.yml`) and one extra dependency
  (`python-dotenv`) to keep track of
