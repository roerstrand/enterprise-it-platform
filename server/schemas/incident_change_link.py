from pydantic import BaseModel

class IncidentChangeLinkSchema(BaseModel):
    change_id: int
