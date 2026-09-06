from app.db import DbSession
from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.services.metrics_service import load_latest_monitor_statuses
from app.metrics import set_monitor_statuses


router = APIRouter(tags=["metrics"])


@router.get("/metrics", include_in_schema=False)
def read_metrics(db: DbSession) -> Response:
    statuses = load_latest_monitor_statuses(db)
    set_monitor_statuses(statuses)
    
    return Response(
        content=generate_latest(),
        headers={"Content-Type": CONTENT_TYPE_LATEST},
    )
    