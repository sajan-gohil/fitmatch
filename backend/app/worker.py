from app.core.celery_app import celery_app


@celery_app.task(name="fitmatch.worker.ping")
def ping() -> str:
    return "pong"
