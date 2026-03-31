from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitMatch API"
    env: Literal["development", "staging", "production"] = Field(
        default="development", alias="FITMATCH_ENV"
    )
    api_prefix: str = Field(default="/api", alias="FITMATCH_API_PREFIX")
    database_url: str = Field(
        default="postgresql://fitmatch:fitmatch@localhost:5432/fitmatch",
        alias="FITMATCH_DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="FITMATCH_REDIS_URL")
    log_level: str = Field(default="INFO", alias="FITMATCH_LOG_LEVEL")
    error_reporting_dsn: str | None = Field(
        default=None, alias="FITMATCH_ERROR_REPORTING_DSN"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
