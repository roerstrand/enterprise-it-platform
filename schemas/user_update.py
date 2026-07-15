from pydantic import BaseModel

class UserUpdateSchema(BaseModel):
    name: str
    email: str