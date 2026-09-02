from fastapi import APIRouter, status, HTTPException
from app.db import DbSession
from app.models import Monitor, Incident
from app.schemas import IncidentRead, MonitorCreate, MonitorRead, MonitorUpdate

router = APIRouter(prefix="/monitors", tags=["monitors"])

@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
def create_monitor(monitor_in: MonitorCreate, db: DbSession):
    """Add a new monitor"""
    monitor_data = monitor_in.model_dump(mode="json")
    monitor = Monitor(**monitor_data)

    db.add(monitor)
    db.commit()
    db.refresh(monitor)

    return monitor

@router.get("", response_model=list[MonitorRead])
def read_monitors(db: DbSession):
    """List all monitors"""
    return db.query(Monitor).all()

@router.get("/{monitor_id}", response_model=MonitorRead)
def read_monitor(monitor_id: int, db: DbSession):
    """Get a specific monitor"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor

@router.patch("/{monitor_id}", response_model=MonitorRead)
def update_monitor(monitor_id: int, monitor_in: MonitorUpdate, db: DbSession):
    """Update a specific monitor"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    # Update fields if they are provided in the request
    update_data = monitor_in.model_dump(exclude_unset=True, exclude_none=True, mode="json")
    for field, value in update_data.items():
        setattr(monitor, field, value)

    db.commit()
    db.refresh(monitor)

    return monitor

@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monitor(monitor_id: int, db: DbSession):
    """Delete a specific monitor"""
    monitor = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")

    db.delete(monitor)
    db.commit()

    return

@router.get("/{monitor_id}/incidents", response_model=list[IncidentRead])
def read_monitor_incidents(monitor_id: int, db: DbSession):
    """List incidents for a specific monitor"""
    monitor = db.get(Monitor, monitor_id)
    if monitor is None:
        raise HTTPException(status_code=404, detail="Monitor not found")

    return db.query(Incident).filter(Incident.monitor_id == monitor_id).order_by(Incident.started_at.desc(), Incident.id.desc()).all()

    