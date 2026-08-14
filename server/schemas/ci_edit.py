from pydantic import BaseModel

class CIEditSchema(BaseModel):
    name: str
    ci_type: str
    environment: str
    owner_user_id: int | None = None