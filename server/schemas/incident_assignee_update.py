from pydantic import BaseModel

class IncidentAssigneeUpdateSchema(BaseModel):
    # None = unassign
    assignee_user_id: int | None = None
