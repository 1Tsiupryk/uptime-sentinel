from functools import lru_cache
from typing_extensions import Literal 
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, PostgresDsn, computed_field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore"
    )

    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    #Worker settings
    WORKER_POLL_INTERVAL_SECONDS: int = Field(default=5, ge=1, le=300)

    #Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = Field(default=0, ge=0)
    REDIS_SOCKET_TIMEOUT_SECONDS: int = Field(default=2, ge=1, le=30)
    REDIS_LOCK_TIMEOUT_SECONDS: int = Field(default=90, ge=61, le=3600)

    # Database settings
    PROJECT_NAME: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB
        )

@lru_cache
def get_settings() -> Settings:
    return Settings()