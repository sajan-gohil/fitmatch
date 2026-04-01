from app.core.celery_app import celery_app
from app.core.matching import list_top_matches_for_user
from app.core.notifications import (
    all_notification_users,
    evaluate_notifications_for_user,
    run_weekly_digest,
)
from app.core.job_ingestion import ingest_with_retry, scrape_schedule
from app.core.resume_store import list_resume_owners
from app.core.settings import get_settings

settings = get_settings()


@celery_app.task(name="fitmatch.worker.ping")
def ping() -> str:
    return "pong"


@celery_app.task(name="fitmatch.worker.scrape_source")
def scrape_source(source_url: str, payload: dict[str, object]) -> dict[str, object]:
    return ingest_with_retry(
        source_url=source_url,
        payload=payload,
        max_retries=settings.scrape_retry_attempts,
    )


@celery_app.task(name="fitmatch.worker.scrape_schedule")
def scrape_schedule_task() -> tuple[dict[str, str], ...]:
    return scrape_schedule()


@celery_app.task(name="fitmatch.worker.refresh_matches_for_user")
def refresh_matches_for_user(user_email: str, limit: int = 25) -> dict[str, object]:
    matches = list_top_matches_for_user(user_email, limit=limit)
    return {"user_email": user_email, "match_count": len(matches)}


@celery_app.task(name="fitmatch.worker.refresh_incremental_matches")
def refresh_incremental_matches(limit_per_user: int = 25) -> dict[str, object]:
    known_users = list_resume_owners()
    refreshed = 0
    for user_email in known_users:
        if not isinstance(user_email, str) or not user_email:
            continue
        refresh_matches_for_user(user_email=user_email, limit=limit_per_user)
        refreshed += 1
    return {"refreshed_users": refreshed}


@celery_app.task(name="fitmatch.worker.dispatch_notifications_for_user")
def dispatch_notifications_for_user(user_email: str) -> dict[str, object]:
    result = evaluate_notifications_for_user(user_email)
    return result


@celery_app.task(name="fitmatch.worker.dispatch_notifications_incremental")
def dispatch_notifications_incremental() -> dict[str, object]:
    known_users = set(list_resume_owners())
    known_users.update(all_notification_users())
    dispatched = 0
    queued = 0
    for user_email in sorted(known_users):
        if not isinstance(user_email, str) or not user_email:
            continue
        result = dispatch_notifications_for_user(user_email)
        queued += int(result.get("queued", 0))
        dispatched += 1
    return {"dispatched_users": dispatched, "queued_notifications": queued}


@celery_app.task(name="fitmatch.worker.send_weekly_digest")
def send_weekly_digest() -> dict[str, object]:
    return run_weekly_digest()
