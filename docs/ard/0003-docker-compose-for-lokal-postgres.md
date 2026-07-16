# ARD-0003: Docker Compose för lokal PostgreSQL-utveckling

## Status
Accepted

## Datum
2026-07-16

## Kontext
Efter ARD-0001 (PostgreSQL som slutmål) krävs ett reproducerbart sätt att
köra en lokal Postgres-instans för utveckling, utan att manuellt behöva
ange `docker run`-flaggor vid varje uppstart. Datorn har dessutom en native
Windows PostgreSQL-tjänst som redan lyssnar på port 5432, vilket krockar med
en Docker-container på samma port och ger ett maskerat `UnicodeDecodeError`
i psycopg2 istället för ett tydligt autentiseringsfel.

## Beslut
- `docker-compose.yml` i projektroten definierar Postgres-containern
  (`postgres:16`, named volume för persistens, host-port 5433 mappad till
  container-port 5432 för att undvika krock med den native tjänsten).
- En `.env`-fil (git-ignorerad) håller `DATABASE_URL`, laddas via
  `python-dotenv` (`load_dotenv()`) överst i `data/database.py` innan
  `os.getenv("DATABASE_URL", ...)` läses.
- Containern startas/stoppas med `docker compose up -d` / `docker compose down`
  istället för enskilda `docker run`-kommandon.

## Alternativ som övervägdes
- Manuellt `docker run`-kommando vid varje uppstart — avfärdat, svårt att
  komma ihåg flaggor och risk för att råka mappa fel port igen
- Enbart `.env` utan docker-compose — avfärdat, löser inte containerns
  konfiguration, bara anslutningssträngen

## Konsekvenser
- En ny utvecklare kan köra `docker compose up -d` och få rätt databas utan
  att känna till port-krocken i förväg
- `load_dotenv()` skriver inte över en redan satt miljövariabel i sessionen
  — om `$env:DATABASE_URL` satts manuellt med fel port tidigare i samma
  session vinner den över `.env` tills den nollställs
  (`Remove-Item Env:\DATABASE_URL`)
- En extra fil (`docker-compose.yml`) och ett extra beroende
  (`python-dotenv`) att hålla koll på
