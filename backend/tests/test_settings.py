from app.core.settings import Settings


def test_settings_load_from_env(monkeypatch) -> None:
    monkeypatch.setenv("FITMATCH_DATABASE_URL", "postgresql://localhost:5432/fitmatch")
    monkeypatch.setenv("FITMATCH_REDIS_URL", "redis://localhost:6379/0")

    settings = Settings()

    assert settings.database_url == "postgresql://localhost:5432/fitmatch"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.api_prefix == "/api"
    assert "localhost:3000" in settings.cors_origins
    assert settings.auth_provider == "supabase"
    assert settings.resume_storage_bucket == "resumes"
    assert settings.llm_provider == "openai"
    assert settings.embedding_model == "text-embedding-3-small"
    assert settings.embedding_dimensions == 1536
    assert settings.stripe_pro_price_id == "price_pro_monthly"
    assert settings.stripe_lifetime_price_id == "price_lifetime_one_time"
    assert settings.app_url == "http://localhost:3000"
    assert settings.notification_high_match_threshold == 80.0
    assert settings.notification_resume_stale_days == 90
    assert settings.notification_digest_weekday == 0
    assert settings.notification_digest_hour_utc == 14
    assert settings.notification_default_min_salary == 0
    assert settings.affiliate_catalog_sync_interval_hours == 24
    assert settings.affiliate_stale_catalog_fallback_hours == 168
    assert settings.scrape_rate_limit_per_minute == 120
    assert settings.scrape_queue_partitions == 4
    assert settings.lifetime_api_daily_quota == 200
