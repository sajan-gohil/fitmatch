from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.logging import configure_logging
from app.core.redis import close_redis_client
from app.core.settings import get_settings

settings = get_settings()

configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix=settings.api_prefix)


@app.on_event("shutdown")
def shutdown_event() -> None:
    close_redis_client()
