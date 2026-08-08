from pydantic import BaseModel

class CICreateSchema(BaseModel):
    name: str
    ci_type: str
    environment: str
    owner_user_id: int | None = None
