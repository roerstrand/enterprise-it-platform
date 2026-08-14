from pydantic import BaseModel

class IncidentEditSchema(BaseModel):
    title: str
    description: str
    severity: str
    ci_id: int
