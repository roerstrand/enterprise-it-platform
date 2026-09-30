import asyncio

from data.database import get_db_context
from repositories.incident_repository import get_all_incidents_from_db
from grpc_servers.incident_server import _generate_and_store_summary

# Engangsscript: CreateIncident triggar AI-jobbet bara vid skapandet, ingen retroaktiv
# koersling finns. Det haer kor samma logik (_generate_and_store_summary) mot alla
# incidenter som aldrig fick en lyckad summary (status "pending" fran start, eller
# "failed" fran tidigare forsok innan Foundry Local var uppe).

async def main():
    async with get_db_context() as db:
        incidents = await get_all_incidents_from_db(db)

    targets = [i for i in incidents if i.ai_summary_status != "ready"]
    print(f"{len(targets)} av {len(incidents)} incidenter saknar en lyckad AI-summary.")

    for incident in targets:
        print(f"  #{incident.id} '{incident.title}' (status: {incident.ai_summary_status}) ...", end=" ")
        await _generate_and_store_summary(incident.id, incident.title, incident.description, incident.ci_id)
        print("klart")

    print("Backfill klar.")

if __name__ == "__main__":
    asyncio.run(main())
