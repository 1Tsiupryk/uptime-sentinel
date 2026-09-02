from app.services.checker import check_monitor
from app.models import Monitor, CheckResult
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.services.incident_manager import process_check_result
import logging

logger = logging.getLogger(__name__)

def run_monitor_check(monitor: Monitor, db: Session) -> CheckResult:
    result = check_monitor(monitor)

    check_result = CheckResult(
        monitor_id=monitor.id,
        status=result.status,
        status_code=result.status_code,
        latency_ms=result.latency_ms,
        error=result.error,
    )
    try:
        db.add(check_result)
        db.flush()

        incident = process_check_result(db, check_result)

        incident_opened = (
            incident is not None
            and check_result.status == "down"
            and incident.opening_check_id == check_result.id
        )

        incident_resolved = (
            incident is not None
            and check_result.status == "up"
            and incident.closing_check_id == check_result.id
        )

        db.commit()
        db.refresh(check_result)
    except SQLAlchemyError:
        db.rollback()
        raise

    if incident is not None:
        if incident_opened:
            logger.warning(
                "Incident opened incident_id=%s monitor_id=%s opening_check_id=%s",
                incident.id,
                monitor.id,
                check_result.id,
            )

        if incident_resolved:
            logger.info(
                "Incident resolved incident_id=%s monitor_id=%s closing_check_id=%s",
                incident.id,
                monitor.id,
                check_result.id,
            )

    return check_result