from pydantic import BaseModel

class ChangeCreateSchema(BaseModel):
    title: str
    description: str
    risk_level: str
    ci_id: int
