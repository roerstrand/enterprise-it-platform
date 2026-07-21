# ARD-0002: Flerlagersarkitektur för endpoints

## Status
Accepted

## Datum
2026-07-15

## Kontext
Projektet ska växa med fler resurser och eventuellt fler microservices. Vi
behöver ett konsekvent mönster för hur en request tar sig genom kodbasen, så
att HTTP-hantering, affärslogik och databasåtkomst inte blandas ihop i samma
funktion.

## Beslut
Varje resurs delas upp i fyra lager, med ett strikt beroende nedåt:

```
routers/<resurs>.py       (HTTP-endpoints, Depends-injection, statuskoder)
  └── services/<resurs>_service.py    (affärslogik)
        └── repositories/<resurs>_repository.py  (DB-queries)
              └── data/models/<resurs>_model.py   (SQLAlchemy-modell)
```

- Routers känner bara till services, aldrig repositories eller modeller direkt.
- Services känner bara till repositories, aldrig SQLAlchemy-queries direkt.
- Repositories är enda stället som pratar med databasen.
- DB-sessionen injiceras via `Depends(get_db)` i routern och skickas ner
  som första argument (`db: Session`) genom hela kedjan.

Mönstret gäller för alla nya resurser framöver, inte bara `users`.

## Alternativ som övervägdes
- Allt i routerfunktionen (endpoint pratar direkt med DB) — avfärdat, blir
  snabbt otestbart och svårt att återanvända logik mellan HTTP och gRPC
- Generisk repository/service-bas-klass — avfärdat för tidigt, för få
  resurser ännu för att motivera abstraktionen

## Konsekvenser
- Ny resurs kräver fyra nya filer (model, repository, service, router) —
  mer boilerplate men tydlig ansvarsfördelning
- Affärslogiken i services kan återanvändas av både REST-routern och en
  framtida gRPC-server utan att duplicera DB-kod
- Enklare att testa services/repositories isolerat med mockad `db`-session
