# ARD-0012: uv for Python dependency management

## Status
Accepted

## Date
2026-08-08

## Context
While writing Dockerfiles for the Python services (ARD-0011), no `requirements.txt` or equivalent dependency manifest existed anywhere in the repository — dependencies had been installed into `.venv` incrementally over weeks with nothing recording which packages, or which versions, were actually needed. A working `requirements.txt` had to be generated on the spot via `pip freeze` against the existing `.venv`, and even then required manual correction: four unused packages left over from an earlier, abandoned SDK integration (`foundry-local-core`, `foundry-local-sdk`, `onnxruntime-core`, `onnxruntime-genai-core`, plus their transitive `binary` dependency) had to be identified via grep and removed before the list was trustworthy.

Plain `pip install <package>` does not update `requirements.txt` or any other manifest — unlike `npm install <package>` (auto-updates `package.json`) or `dotnet add package <package>` (auto-updates the `.csproj`), both patterns already present elsewhere in this repository (the vanilla-JS demo tooling and the C# services respectively). This is a structural gap in the plain-pip workflow, not a one-off mistake, and it had already caused exactly the failure it would be expected to cause.

## Decision
Python dependency management moves to **uv**: `pyproject.toml` (the dependency list, equivalent to `package.json`) plus `uv.lock` (exact resolved versions including transitive dependencies, equivalent to `package-lock.json`) replace `requirements.txt`. `requirements.txt` is deleted.

- `pyproject.toml` created via `uv init --bare` (creates only the manifest, no scaffolding that could collide with the existing `main.py`).
- Dependencies imported in one pass via `uv add -r requirements.txt` against the corrected package list, then `requirements.txt` removed.
- Dockerfiles copy the `uv`/`uvx` binaries from `ghcr.io/astral-sh/uv`'s official image (`COPY --from=ghcr.io/astral-sh/uv:latest`) rather than installing uv via pip, and use `uv sync --frozen --no-install-project` (dependencies only, for Docker layer caching) followed by `uv sync --frozen` after the code is copied in, and `uv run <command>` in place of a bare `python`/`uvicorn` invocation.
- Local development continues to use the same `.venv` at the repo root; `uv` manages it directly (confirmed working: `.venv/Scripts/python.exe` still resolves and imports correctly after the migration), so `watchmedo`'s existing invocation pattern (pointing at `.venv/Scripts/python.exe`) is unaffected.

## Alternatives considered
- **Poetry.** Comparable auto-tracking behavior to uv (also maintains a manifest + lock file automatically on install). Not chosen — uv is a single native binary with no separate Python-based install step, and is faster for both dependency resolution and Docker image builds, which matters directly for the inner loop this ARD is trying to improve.
- **Continue with plain `pip` + a manually-maintained `requirements.txt`.** Rejected outright — this is the status quo that produced the missing-manifest problem in the first place; there is no mechanism under this approach that prevents the same drift from recurring.

## Consequences
- The dependency manifest can no longer silently drift from what's actually installed — `uv add`/`uv remove` keep `pyproject.toml` and `uv.lock` in sync automatically, matching the behavior already relied on for the Node and .NET parts of this repository.
- Docker builds are faster (`uv sync` resolves and installs faster than `pip install -r requirements.txt`), which matters more now that the inner loop for containerized services includes a rebuild step (ARD-0011).
- `psycopg2` (the source-build package) was replaced with `psycopg2-binary` during this same pass — unrelated to uv itself, but surfaced by the first from-scratch Docker build, since `python:3.13-slim` lacks the C compiler and Postgres headers `psycopg2` needs to build from source.
- Any new machine setting up this repository now needs `uv` installed (in addition to Python itself); plain `pip install -r requirements.txt` is no longer sufficient or accurate, since that file no longer exists.
