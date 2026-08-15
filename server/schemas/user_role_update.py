from pydantic import BaseModel, field_validator

from auth.security import ROLES

class UserRoleUpdateSchema(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def role_must_be_known(cls, value: str) -> str:
        if value not in ROLES:
            raise ValueError(f"role must be one of {ROLES}")
        return value
