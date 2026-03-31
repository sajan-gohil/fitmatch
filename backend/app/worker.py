from app.core.celery_app import celery_app
from app.core.job_ingestion import ingest_with_retry, scrape_schedule
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
