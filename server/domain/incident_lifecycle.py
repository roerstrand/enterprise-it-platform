STATUSES = ("open", "in_progress", "resolved", "closed")

# Explicit lifecycle: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED, strictly forward, no skipping.
# CLOSED is terminal - no outgoing transitions.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress"},
    "in_progress": {"resolved"},
    "resolved": {"closed"},
    "closed": set(),
}

class InvalidStatusTransition(Exception):
    def __init__(self, current_status: str, new_status: str):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(f"Cannot transition incident from '{current_status}' to '{new_status}'")

def validate_transition(current_status: str, new_status: str) -> None:
    if new_status not in STATUSES:
        raise InvalidStatusTransition(current_status, new_status)
    # Samma status = no-op, inte ett fel (t.ex. AI föreslår status som redan gäller)
    if new_status == current_status:
        return
    if new_status not in ALLOWED_TRANSITIONS.get(current_status, set()):
        raise InvalidStatusTransition(current_status, new_status)

SEVERITIES = ("low", "medium", "high", "critical")

class InvalidSeverity(Exception):
    def __init__(self, severity: str):
        self.severity = severity
        super().__init__(f"Invalid severity '{severity}', must be one of {SEVERITIES}")

def validate_severity(severity: str) -> str:
    normalized = (severity or "").lower()
    if normalized not in SEVERITIES:
        raise InvalidSeverity(severity)
    return normalized
