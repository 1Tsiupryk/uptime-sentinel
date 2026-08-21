from app.services.check_runner import run_monitor_check
from datetime import datetime
from fastapi import APIRouter, status, HTTPException
from app.schemas import CheckResultRead
from app.models import CheckResult, Monitor
from app.db import DbSession

router = APIRouter(prefix="/monitors", tags=["checks"])

@router.post("/{monitor_id}/check", response_model=CheckResultRead, status_code=status.HTTP_201_CREATED)
def trigger_check(monitor_id: int, db: DbSession):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return run_monitor_check(monitor, db)

@router.get("/{monitor_id}/checks", response_model=list[CheckResultRead])
def get_checks(monitor_id: int, db: DbSession):
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()

    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    
    return (
        db.query(CheckResult)
        .filter(CheckResult.monitor_id == monitor_id)
        .order_by(CheckResult.checked_at.desc(), CheckResult.id.desc())
        .all()
    )
