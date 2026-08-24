from datetime import datetime, timedelta, timezone

# Enda stället policyn definieras. En framtida "gör SLA konfigurerbart" behöver bara byta ut
# get_sla_target() mot en DB-uppslagning (t.ex. per severity, per kund) - allt annat i den här
# filen och alla anropare (bara IncidentResponse-byggaren i incident_server.py) förblir oförändrade.
SLA_TARGETS_MINUTES: dict[str, dict[str, int]] = {
    "critical": {"response": 15, "resolution": 4 * 60},
    "high": {"response": 60, "resolution": 8 * 60},
    "medium": {"response": 4 * 60, "resolution": 24 * 60},
    "low": {"response": 8 * 60, "resolution": 72 * 60},
}

# Andel av kvarvarande tid mot nästa deadline under vilken tillståndet blir "at_risk" istället för "on_track"
AT_RISK_THRESHOLD = 0.2

def get_sla_target(severity: str) -> dict[str, int]:
    return SLA_TARGETS_MINUTES.get((severity or "").lower(), SLA_TARGETS_MINUTES["low"])

def compute_sla(
    created_at: datetime,
    severity: str,
    first_response_at: datetime | None,
    resolved_at: datetime | None,
    status: str,
    now: datetime | None = None,
) -> dict:
    now = now or datetime.now(timezone.utc)
    target = get_sla_target(severity)
    response_deadline = created_at + timedelta(minutes=target["response"])
    resolution_deadline = created_at + timedelta(minutes=target["resolution"])

    response_breached = (first_response_at or now) > response_deadline
    if resolved_at is not None:
        resolution_breached = resolved_at > resolution_deadline
    else:
        resolution_breached = status not in ("resolved", "closed") and now > resolution_deadline

    is_done = status in ("resolved", "closed")
    if is_done:
        state = "breached" if (response_breached or resolution_breached) else "met"
        remaining_seconds = 0
    elif response_breached or resolution_breached:
        state = "breached"
        # Negativ = hur långt förbi deadline vi är
        active_deadline = response_deadline if not first_response_at else resolution_deadline
        remaining_seconds = int((active_deadline - now).total_seconds())
    else:
        active_deadline = response_deadline if not first_response_at else resolution_deadline
        remaining_seconds = int((active_deadline - now).total_seconds())
        target_minutes = target["response"] if not first_response_at else target["resolution"]
        at_risk_window_seconds = target_minutes * 60 * AT_RISK_THRESHOLD
        state = "at_risk" if remaining_seconds <= at_risk_window_seconds else "on_track"

    return {
        "response_deadline": response_deadline,
        "resolution_deadline": resolution_deadline,
        "response_breached": response_breached,
        "resolution_breached": resolution_breached,
        "state": state,
        "remaining_seconds": remaining_seconds,
    }
