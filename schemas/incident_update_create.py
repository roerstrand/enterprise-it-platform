from pydantic import BaseModel

class IncidentUpdateCreateSchema(BaseModel):
    text: str

