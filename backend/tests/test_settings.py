from app.core.settings import Settings


def test_settings_load_from_env(monkeypatch) -> None:
    monkeypatch.setenv("FITMATCH_DATABASE_URL", "postgresql://localhost:5432/fitmatch")
    monkeypatch.setenv("FITMATCH_REDIS_URL", "redis://localhost:6379/0")

    settings = Settings()

    assert settings.database_url == "postgresql://localhost:5432/fitmatch"
    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.api_prefix == "/api"
