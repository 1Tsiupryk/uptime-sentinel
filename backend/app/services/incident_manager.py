from app.models import Incident, CheckResult
from sqlalchemy.orm import Session
from sqlalchemy import select


def process_check_result(
    session: Session,
    check_result: CheckResult
) -> Incident | None:
    open_incident = session.scalar(
        select(Incident).where(
            Incident.monitor_id == check_result.monitor_id,
            Incident.resolved_at.is_(None),
        )
    )

    if check_result.status == "down":
        if open_incident:
            return open_incident

        new_incident = Incident(
            monitor_id=check_result.monitor_id,
            started_at=check_result.checked_at,
            opening_check_id=check_result.id,
        )

        session.add(new_incident)

        return new_incident

    if check_result.status == "up" and open_incident:
        open_incident.resolved_at = check_result.checked_at
        open_incident.closing_check_id = check_result.id
        
        return open_incident
        
    return None
    