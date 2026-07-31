from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

class MonitorBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: HttpUrl
    interval_seconds: int = Field(default=60, ge=10, le=86400)
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    expected_status_code: int = Field(default=200, ge=100, le=599)
    enabled: bool = True

class MonitorCreate(MonitorBase):
    pass

class MonitorRead(MonitorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

class MonitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    url: HttpUrl | None = None
    interval_seconds: int | None = Field(default=None, ge=10, le=86400)
    timeout_seconds: int | None = Field(default=None, ge=1, le=60)
    expected_status_code: int | None = Field(default=None, ge=100, le=599)
    enabled: bool | None = None

