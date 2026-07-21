# ARD-0001: PostgreSQL som slutgiltig databas

## Status
Proposed

## Datum
2026-07-15

## Kontext
Projektet använder idag SQLite för utveckling. SQLite är enkelt att komma igång
med men saknar t.ex. bra stöd för samtidiga skrivningar, saknar riktiga
datatyper för vissa fält, och är inte lämpligt för produktion i en
microservice-miljö.

## Beslut
Vi går mot PostgreSQL som produktionsdatabas. SQLite behålls tills vidare
som lokal utvecklings-/testdatabas.

## Alternativ som övervägdes
- Fortsätta med SQLite i produktion — avfärdat pga bristande samtidighet och skalbarhet
- MySQL — avfärdat, PostgreSQL har bättre stöd för JSON-fält och striktare typning

## Konsekvenser
- SQLAlchemy-modellerna måste vara databas-agnostiska (undvik SQLite-specifika typer)
- Behöver en migrationsstrategi (t.ex. Alembic) innan bytet sker
- Connection string i database.py måste bli miljöberoende (dev=SQLite, prod=PostgreSQL)
