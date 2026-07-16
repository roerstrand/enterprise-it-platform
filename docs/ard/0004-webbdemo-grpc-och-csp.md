# ARD-0004: Webbdemo-klient med gRPC som intern transport och strikt CSP

## Status
Accepted

## Datum
2026-07-16

## Kontext
Ett sätt behövs för att visa att systemet fungerar utan att öppna Swagger,
och för att demonstrera intern gRPC-kommunikation mellan FastAPI-processen
och den befintliga microservicen (`microservices.py`). Principen för
projektet är att intern kommunikation ska ske via gRPC/Protobuf, aldrig via
REST-till-REST.

## Beslut
- FastAPI (`main.py`) serverar en statisk HTML/CSS/JS-klient under `/demo`.
- Klientens endpoints (`routers/demo.py`) pratar gRPC mot den befintliga
  microservicen istället för att gå via `repository` direkt — en egen
  gRPC-klientmodul (`grpc_clients/user_client.py`) återanvänder samma
  kanal/stub-mönster som redan finns i `grpc_client.py`.
- `microservices.py` fortsätter köra som en separat process (startas för
  sig, parallellt med `uvicorn main:app`), eftersom det är just två skilda
  processer som pratar med varandra som gör demot till en äkta
  microservice-demonstration.
- Säkerhetsheaders och Content-Security-Policy hanteras i en dedikerad
  middleware (`middleware/security_headers.py`), inte utspritt i routrar.
- HTML/CSS/JS struktureras utan inline-kod, så en strikt CSP
  (`script-src 'self'`, `style-src 'self'`, ingen `unsafe-inline`) fungerar
  utan undantag.

## Alternativ som övervägdes
- Demo-endpoints som går direkt mot `repository` — avfärdat, visar inte
  gRPC-flödet och motsäger projektets syfte
- Inline JS/CSS för enkelhetens skull — avfärdat, omöjliggör en strikt CSP
- Full isolation med separat databas/repository-kod per tjänst — avfärdat
  för det här projektet, se konsekvens nedan

## Konsekvenser
- Kräver att `microservices.py` körs som separat process för att `/demo`
  ska fungera — ett rimligt fel måste hanteras i UI om den processen är
  nere (gRPC-anropet misslyckas)
- `main.py` (FastAPI) och `microservices.py` (gRPC) delar fortfarande samma
  `repositories/`-kod och samma databas. Det är en medveten förenkling för
  ett lärprojekt i en monorepo — en "renodlad" microservice-arkitektur
  skulle låta varje tjänst äga sin egen databasåtkomst och bara dela ett
  kontrakt (proto-filen), inte Python-moduler. Att bygga ut det nu vore ett
  separat, större beslut och görs inte som en del av den här funktionen.
