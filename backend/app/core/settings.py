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
    cors_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="FITMATCH_CORS_ORIGINS",
    )
    auth_provider: str = Field(default="supabase", alias="FITMATCH_AUTH_PROVIDER")
    resume_storage_bucket: str = Field(
        default="resumes", alias="FITMATCH_RESUME_STORAGE_BUCKET"
    )
    llm_provider: str = Field(default="openai", alias="FITMATCH_LLM_PROVIDER")
    embedding_model: str = Field(default="text-embedding-3-small", alias="FITMATCH_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=1536, alias="FITMATCH_EMBEDDING_DIMENSIONS")
    scrape_retry_attempts: int = Field(default=3, alias="FITMATCH_SCRAPE_RETRY_ATTEMPTS")
    scrape_tier1_interval_minutes: int = Field(
        default=360,
        alias="FITMATCH_SCRAPE_TIER1_INTERVAL_MINUTES",
    )
    scrape_tier2_interval_minutes: int = Field(
        default=1440,
        alias="FITMATCH_SCRAPE_TIER2_INTERVAL_MINUTES",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
