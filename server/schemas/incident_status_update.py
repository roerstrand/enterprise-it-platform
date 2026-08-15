from pydantic import BaseModel

class IncidentStatusUpdateSchema(BaseModel):
    status: str
