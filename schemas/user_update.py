from pydantic import BaseModel, EmailStr

class UserUpdateSchema(BaseModel):
    name: str
    email: EmailStr