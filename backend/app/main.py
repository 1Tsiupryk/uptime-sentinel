from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.monitors import router as monitors_router

app = FastAPI()
app.include_router(health_router)
app.include_router(monitors_router)