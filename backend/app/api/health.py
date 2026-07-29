from fastapi import APIRouter, HTTPException
from app.db import check_database_connection

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/ready")
def ready_check():
    if not check_database_connection():
        raise HTTPException(
            status_code=503,
            detail="Database connection error."
            )
    
    return {"status": "ready"}