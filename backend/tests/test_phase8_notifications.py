from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
import pytest

from app.core.job_ingestion import IngestionPipeline, reset_ingestion_state
from app.core.notifications import (
    get_email_outbox,
    reset_notification_state,
    run_weekly_digest,
)
from app.main import app
from app.worker import dispatch_notifications_incremental

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()
    reset_notification_state()


def _auth_headers(email: str = "phase8@example.com") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "provider": "magic_link"})
    assert login.status_code == 202
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _onboard(headers: dict[str, str], locations: list[str] | None = None) -> None:
    response = client.post(
        "/api/onboarding",
        headers=headers,
        json={
            "target_roles": ["Data Engineer"],
            "preferred_locations": locations or ["Toronto"],
            "work_type_preferences": ["remote"],
        },
    )
    assert response.status_code == 200


def _upload_resume(headers: dict[str, str], file_name: str = "data_resume.pdf") -> None:
    response = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": (file_name, b"%PDF-1.4 phase8", "application/pdf")},
    )
    assert response.status_code == 201


def _ingest_jobs_for_notifications(deadline_days: int = 2) -> None:
    deadline = (datetime.now(UTC) + timedelta(days=deadline_days)).isoformat()
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://boards.greenhouse.io/fitmatch",
        {
            "company": "FitMatch",
            "jobs": [
                {
                    "id": "phase8-role-1",
                    "title": "Senior Data Engineer",
                    "location": {"name": "Toronto, ON"},
                    "content": "Build data pipelines using Python and SQL.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase8-role-1",
                    "updated_at": "2026-04-01T08:00:00Z",
                    "salary_min": 130000,
                    "application_deadline": deadline,
                }
            ],
        },
    )


def test_phase8_preferences_api_round_trip() -> None:
    headers = _auth_headers("phase8-prefs@example.com")

    initial = client.get("/api/notifications/preferences", headers=headers)
    assert initial.status_code == 200
    assert "channels" in initial.json()

    updated = client.put(
        "/api/notifications/preferences",
        headers=headers,
        json={
            "channels": ["email", "in_app"],
            "enabled_triggers": ["high_match", "watchlist", "salary_threshold", "deadline"],
            "quiet_hours": {"start": 22, "end": 7},
            "min_match_score": 70,
            "min_salary": 120000,
            "watchlist_companies": ["FitMatch"],
        },
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["min_match_score"] == 70
    assert payload["min_salary"] == 120000
    assert payload["watchlist_companies"] == ["FitMatch"]


def test_phase8_dispatch_generates_feed_and_email_events() -> None:
    email = "phase8-dispatch@example.com"
    headers = _auth_headers(email)
    _onboard(headers)
    _upload_resume(headers)
    _ingest_jobs_for_notifications()

    prefs = client.put(
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
    assert prefs.status_code == 200

    dispatch = dispatch_notifications_incremental()
    assert dispatch["dispatched_users"] >= 1
    assert dispatch["queued_notifications"] >= 1

    feed = client.get("/api/notifications", headers=headers)
    assert feed.status_code == 200
    payload = feed.json()
    assert payload["total"] >= 1
    assert payload["unread_count"] >= 1
    triggers = {item["trigger"] for item in payload["items"]}
    assert "high_match" in triggers

    outbox = get_email_outbox()
    assert any(item["user_email"] == email for item in outbox)


def test_phase8_feed_read_unread_state() -> None:
    email = "phase8-read@example.com"
    headers = _auth_headers(email)
    _onboard(headers)
    _upload_resume(headers)
    _ingest_jobs_for_notifications()
    client.put(
        "/api/notifications/preferences",
        headers=headers,
        json={
            "channels": ["in_app"],
            "enabled_triggers": ["high_match"],
            "quiet_hours": {"start": 1, "end": 2},
            "min_match_score": 60,
        },
    )

    dispatch_notifications_incremental()

    feed = client.get("/api/notifications", headers=headers)
    assert feed.status_code == 200
    first = feed.json()["items"][0]

    mark = client.patch(f"/api/notifications/{first['id']}", headers=headers, json={"read": True})
    assert mark.status_code == 200
    assert mark.json()["read"] is True

    unread = client.get("/api/notifications?unread_only=true", headers=headers)
    assert unread.status_code == 200
    assert all(item["read"] is False for item in unread.json()["items"])


def test_phase8_weekly_digest_runs_on_schedule() -> None:
    email = "phase8-digest@example.com"
    headers = _auth_headers(email)
    _onboard(headers)
    _upload_resume(headers)
    _ingest_jobs_for_notifications()
    client.put("/api/notifications/preferences", headers=headers, json={"channels": ["email"]})

    scheduled_time = datetime(2026, 3, 30, 14, 0, tzinfo=UTC)  # Monday 14:00 UTC
    result = run_weekly_digest(now_utc=scheduled_time)
    assert result["reason"] == "scheduled"
    assert result["sent"] >= 1

    outbox = get_email_outbox()
    assert any(item["subject"] == "Your weekly FitMatch digest" for item in outbox)
