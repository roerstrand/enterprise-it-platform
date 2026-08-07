from pydantic import BaseModel

class IncidentCreateSchema(BaseModel):
    title: str
    description: str
    severity: str
    ci_id: int