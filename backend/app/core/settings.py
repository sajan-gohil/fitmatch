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
    stripe_secret_key: str | None = Field(default=None, alias="FITMATCH_STRIPE_SECRET_KEY")
    stripe_webhook_secret: str | None = Field(default=None, alias="FITMATCH_STRIPE_WEBHOOK_SECRET")
    stripe_pro_price_id: str = Field(default="price_pro_monthly", alias="FITMATCH_STRIPE_PRO_PRICE_ID")
    stripe_lifetime_price_id: str = Field(
        default="price_lifetime_one_time",
        alias="FITMATCH_STRIPE_LIFETIME_PRICE_ID",
    )
    app_url: str = Field(default="http://localhost:3000", alias="FITMATCH_APP_URL")
    notification_high_match_threshold: float = Field(
        default=80.0,
        alias="FITMATCH_NOTIFICATION_HIGH_MATCH_THRESHOLD",
    )
    notification_resume_stale_days: int = Field(
        default=90,
        alias="FITMATCH_NOTIFICATION_RESUME_STALE_DAYS",
    )
    notification_digest_weekday: int = Field(
        default=0,
        alias="FITMATCH_NOTIFICATION_DIGEST_WEEKDAY",
    )
    notification_digest_hour_utc: int = Field(
        default=14,
        alias="FITMATCH_NOTIFICATION_DIGEST_HOUR_UTC",
    )
    notification_default_min_salary: int = Field(
        default=0,
        alias="FITMATCH_NOTIFICATION_DEFAULT_MIN_SALARY",
    )
    affiliate_catalog_sync_interval_hours: int = Field(
        default=24,
        alias="FITMATCH_AFFILIATE_CATALOG_SYNC_INTERVAL_HOURS",
    )
    affiliate_stale_catalog_fallback_hours: int = Field(
        default=168,
        alias="FITMATCH_AFFILIATE_STALE_CATALOG_FALLBACK_HOURS",
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
