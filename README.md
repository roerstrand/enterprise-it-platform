# python_microservices

FastAPI-baserad microservice-demo med gRPC som internt datakontrakt och PostgreSQL som databas.

## Arkitektur

Se `docs/ard/` för samtliga arkitekturbeslut (ARD:er). Kortfattat:

- Flerlagersarkitektur: router → service → repository → modell (ARD-0002)
- PostgreSQL som produktionsdatabas, körs lokalt via Docker Compose (ARD-0001, ARD-0003)
- All datahantering sker via gRPC, ingen REST-CRUD (ARD-0005)
- Webbdemo på `/demo` pratar gRPC mot `microservices.py`, med strikt CSP (ARD-0004)

## Arkitekturbeslut (ARD)

Beslut om arkitektur dokumenteras som ARD:er i `docs/ard/`, ett per beslut, numrerade `000X-titel.md`. Mall: `docs/ard/0001-template.md`.

| ARD | Titel | Status |
|-----|-------|--------|
| [0001](docs/ard/0001-postgresql-som-slutmal.md) | PostgreSQL som slutgiltig databas | Proposed |
| [0002](docs/ard/0002-flerlagersarkitektur.md) | Flerlagersarkitektur för endpoints | Accepted |
| [0003](docs/ard/0003-docker-compose-for-lokal-postgres.md) | Docker Compose för lokal PostgreSQL-utveckling | Accepted |
| [0004](docs/ard/0004-webbdemo-grpc-och-csp.md) | Webbdemo-klient med gRPC och strikt CSP | Accepted |
| [0005](docs/ard/0005-ta-bort-rest-crud-endast-grpc.md) | Borttagning av REST-CRUD till förmån för gRPC | Accepted |

Nytt beslut: kopiera mallen, numrera nästa i ordningen, fyll i.

## Köra lokalt

1. `docker compose up -d` — startar PostgreSQL på port 5433
2. `.env` med `DATABASE_URL` måste finnas (git-ignorerad, se ARD-0003)
3. `python microservices.py` — startar gRPC-servern
4. `uvicorn main:app --reload` — startar FastAPI, webbdemo på `/demo`
