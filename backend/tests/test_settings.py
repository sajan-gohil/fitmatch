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
