from fastapi import APIRouter, status

from app.core.redis import get_redis_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", status_code=status.HTTP_200_OK)
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", status_code=status.HTTP_200_OK)
def ready() -> dict[str, str]:
    redis_ok = False
    try:
        redis_ok = bool(get_redis_client().ping())
    except Exception:
        redis_ok = False

    return {
        "status": "ok" if redis_ok else "degraded",
        "redis": "ok" if redis_ok else "unreachable",
    }
