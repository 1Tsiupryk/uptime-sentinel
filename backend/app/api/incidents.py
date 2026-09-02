from fastapi import APIRouter, HTTPException
from app.db import DbSession
from app.models import Incident
from app.schemas import IncidentRead
from typing import Literal

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.get("", response_model=list[IncidentRead])
def read_incidents(db: DbSession, status: Literal["open", "resolved"] | None = None):
    query = db.query(Incident)

    if status == "open":
        query = query.filter(Incident.resolved_at.is_(None))
    elif status == "resolved":
        query = query.filter(Incident.resolved_at.is_not(None))

    return query.order_by(Incident.started_at.desc(), Incident.id.desc()).all()

@router.get("/{incident_id}", response_model=IncidentRead)
def read_incident(incident_id: int, db: DbSession):
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident