from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CheckResult, Monitor

def load_latest_monitor_statuses(db: Session) -> list[tuple[int, str]]:
    latest_check_id = (
        select(CheckResult.id)
        .where(CheckResult.monitor_id == Monitor.id)
        .order_by(CheckResult.checked_at.desc(), CheckResult.id.desc())
        .limit(1)
        .correlate(Monitor)
        .scalar_subquery()
    )
    
    stmt = (
        select(Monitor.id, CheckResult.status)
        .select_from(Monitor)
        .join(
            CheckResult,
            CheckResult.id == latest_check_id
        )
        .where(Monitor.enabled.is_(True))
    )
    
    rows = db.execute(stmt).tuples().all()
    return list(rows)
    
    