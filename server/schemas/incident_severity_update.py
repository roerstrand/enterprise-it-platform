from pydantic import BaseModel

class IncidentSeverityUpdateSchema(BaseModel):
    severity: str
