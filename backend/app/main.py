from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.checks import router as checks_router
from app.api.health import router as health_router
from app.api.monitors import router as monitors_router
from app.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(monitors_router)
app.include_router(checks_router)