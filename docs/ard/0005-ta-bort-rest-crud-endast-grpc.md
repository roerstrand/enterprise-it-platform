# ARD-0005: Borttagning av REST-CRUD till förmån för gRPC som enda datakontrakt

## Status
Accepted

## Datum
2026-07-18

## Kontext
`routers/users.py` → `services/user_service.py` → `repositories/user_repository.py`
har funnits sedan projektets start, som ett resultat av att REST-CRUD:en och
gRPC-servern byggdes som två separata lärövningar i samma repo, utan en
gemensam arkitektonisk linje från början. Efter ARD-0002 (lagerarkitektur)
och ARD-0004 (gRPC som enda interna transport för webbdemot) blev
motsättningen tydlig: REST-endpointen skriver direkt mot databasen, helt
vid sidan av det gRPC-kontrakt som är tänkt att utgöra tjänstegränsen.

En microservice-arkitekturs syfte är att data bara nås genom ett definierat
kontrakt mellan tjänster (här gRPC/Protobuf). En REST-endpoint som skriver
till samma tabell utan att gå via det kontraktet gör att gränsen kan
kringgås — vilket redan orsakat ett konkret problem: REST- och gRPC-vägarna
behövde uppdateras separat för lösenordshashning och hann gå isär innan
båda fixades.

## Beslut
`routers/users.py` och `services/user_service.py` tas bort. All skapande
och läsning av användare sker uteslutande via gRPC (`microservices.py`),
antingen genom webbdemot (`routers/demo.py`, se ARD-0004) eller
testskriptet `grpc_client.py`. `repositories/user_repository.py` och
`data/models/user_model.py` behålls — de används fortfarande internt av
`microservices.py`. `schemas/user_create.py` behålls och återanvänds för
validering av demots create-endpoint. `schemas/user_update.py` tas bort
(blir dödkod, ingen uppdateringsväg finns i gRPC-kontraktet).

## Alternativ som övervägdes
- Behålla REST men spärra den i produktion (t.ex. bunden till localhost
  eller bakom en miljövariabel) — avfärdat. Löser inte grundproblemet
  (gränsen kan fortfarande kringgås lokalt/under utveckling) och är bara
  komplexitet för ett skydd som redan finns genom att ta bort ytan helt.
- Behålla REST som ett rent utvecklarverktyg för snabb manuell testning
  (curl/Swagger) — avfärdat. Undergräver definitionsmässigt poängen med
  microservice-gränsen, inte bara operationellt, och den konkreta
  divergensbuggen visar att den reella kostnaden är verklig, inte
  hypotetisk.

## Konsekvenser
- Ingen REST-CRUD kvar för `users` — `/docs` (Swagger) tappar sin
  användarhantering, manuell testning sker via `/demo` eller
  `grpc_client.py` istället
- En enda kodväg (gRPC → repository) att hålla korrekt, istället för två
  som kan gå isär
- `main.py` behöver uppdateras för att inte längre inkludera
  `routers.users`
