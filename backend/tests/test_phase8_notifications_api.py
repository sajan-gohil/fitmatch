from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
import pytest

from app.core.job_ingestion import IngestionPipeline, reset_ingestion_state
from app.core.notifications import reset_notification_state
from app.main import app
from app.worker import dispatch_notifications_incremental

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()
    reset_notification_state()


def _auth_headers(email: str = "phase8-api@example.com") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "provider": "magic_link"})
    assert login.status_code == 202
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _onboard(headers: dict[str, str]) -> None:
    response = client.post(
        "/api/onboarding",
        headers=headers,
        json={
            "target_roles": ["Data Engineer"],
            "preferred_locations": ["Toronto"],
            "work_type_preferences": ["remote"],
        },
    )
    assert response.status_code == 200


def _upload_resume(headers: dict[str, str]) -> None:
    response = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": ("data_resume.pdf", b"%PDF-1.4 phase8", "application/pdf")},
    )
    assert response.status_code == 201


def _ingest_job() -> None:
    deadline = (datetime.now(UTC) + timedelta(days=2)).isoformat()
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://boards.greenhouse.io/fitmatch",
        {
            "company": "FitMatch",
            "jobs": [
                {
                    "id": "phase8-api-job-1",
                    "title": "Senior Data Engineer",
                    "location": {"name": "Toronto, ON"},
                    "content": "Build data systems using Python and SQL.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase8-api-job-1",
                    "updated_at": "2026-04-01T08:00:00Z",
                    "salary_min": 125000,
                    "application_deadline": deadline,
                }
            ],
        },
    )


def test_phase8_notifications_preferences_requires_auth() -> None:
    response = client.get("/api/notifications/preferences")
    assert response.status_code == 401


def test_phase8_notifications_feed_and_read_flow() -> None:
    headers = _auth_headers("phase8-api-flow@example.com")
    _onboard(headers)
    _upload_resume(headers)
    _ingest_job()

    save = client.put(
        "/api/notifications/preferences",
        headers=headers,
        json={
            "channels": ["email", "in_app"],
            "enabled_triggers": ["high_match", "watchlist", "salary_threshold", "deadline"],
            "quiet_hours": {"start": 1, "end": 2},
            "min_match_score": 60,
            "min_salary": 100000,
            "watchlist_companies": ["FitMatch"],
        },
    )
    assert save.status_code == 200

    dispatch = dispatch_notifications_incremental()
    assert dispatch["queued_notifications"] >= 1

    feed = client.get("/api/notifications", headers=headers)
    assert feed.status_code == 200
    payload = feed.json()
    assert payload["total"] >= 1
    first_id = payload["items"][0]["id"]

    mark_read = client.patch(f"/api/notifications/{first_id}", headers=headers, json={"read": True})
    assert mark_read.status_code == 200
    assert mark_read.json()["read"] is True

    unread = client.get("/api/notifications?unread_only=true", headers=headers)
    assert unread.status_code == 200
    assert all(item["read"] is False for item in unread.json()["items"])
