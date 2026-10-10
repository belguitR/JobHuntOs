from functools import lru_cache

from pydantic import Field, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Job Hunt OS API"
    environment: str = "development"
    database_url: PostgresDsn
    google_client_id: str
    session_signing_key: SecretStr = Field(min_length=32)
    session_cookie_secure: bool = True
    session_duration_seconds: int = Field(default=28_800, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="JOB_HUNT_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
