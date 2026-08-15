from pydantic import BaseModel

class UserResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    role: str

    model_config = {"from_attributes": True}

