from app.services.checker import check_monitor
from app.models import Monitor, CheckResult
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

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
        db.commit()
        db.refresh(check_result)
    except SQLAlchemyError:
        db.rollback()
        raise

    return check_result