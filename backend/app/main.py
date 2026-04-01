from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.affiliate import router as affiliate_router
from app.api.billing import router as billing_router
from app.api.growth import router as growth_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.lifetime_api import router as lifetime_api_router
from app.api.matches import router as matches_router
from app.api.notifications import router as notifications_router
from app.api.onboarding import router as onboarding_router
from app.api.platform_extensions import router as platform_extensions_router
from app.api.resume import router as resume_router
from app.api.resume_intelligence import router as resume_intelligence_router
from app.core.logging import configure_logging
from app.core.redis import close_redis_client
from app.core.settings import get_settings

settings = get_settings()

configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_redis_client()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(billing_router, prefix=settings.api_prefix)
app.include_router(onboarding_router, prefix=settings.api_prefix)
app.include_router(resume_router, prefix=settings.api_prefix)
app.include_router(resume_intelligence_router, prefix=settings.api_prefix)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(matches_router, prefix=settings.api_prefix)
app.include_router(notifications_router, prefix=settings.api_prefix)
app.include_router(affiliate_router, prefix=settings.api_prefix)
app.include_router(growth_router, prefix=settings.api_prefix)
app.include_router(lifetime_api_router, prefix=settings.api_prefix)
app.include_router(platform_extensions_router, prefix=settings.api_prefix)
