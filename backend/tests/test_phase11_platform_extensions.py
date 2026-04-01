from __future__ import annotations

import json
import time

from fastapi.testclient import TestClient
import pytest

from app.core.billing import apply_webhook_event
from app.core.job_ingestion import IngestionPipeline, reset_ingestion_state
from app.core.notifications import reset_notification_state
from app.core.phase11_extensions import reset_phase11_state
from app.main import app
from app.worker import dispatch_notifications_incremental

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()
    reset_notification_state()
    reset_phase11_state()


def _auth_headers(email: str = "phase11@example.com") -> dict[str, str]:
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
            "preferred_locations": ["Austin"],
            "work_type_preferences": ["remote"],
        },
    )
    assert response.status_code == 200


def _upload_resume(headers: dict[str, str]) -> None:
    response = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": ("phase11_resume.pdf", b"%PDF-1.4 phase11", "application/pdf")},
    )
    assert response.status_code == 201


def _ingest_phase11_jobs() -> None:
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://boards.greenhouse.io/fitmatch",
        {
            "company": "FitMatch",
            "jobs": [
                {
                    "id": "phase11-job-1",
                    "title": "Senior Data Engineer",
                    "location": {"name": "Austin, TX"},
                    "content": "Build data platforms with Python and SQL.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase11-job-1",
                    "updated_at": "2026-04-01T08:00:00Z",
                    "salary_min": 135000,
                },
                {
                    "id": "phase11-job-2",
                    "title": "Data Engineer",
                    "location": {"name": "Austin, TX"},
                    "content": "Own data modeling and reporting.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase11-job-2",
                    "updated_at": "2026-04-01T08:05:00Z",
                    "salary_min": 120000,
                },
            ],
        },
    )


def test_phase11_slack_preferences_and_event_queue() -> None:
    headers = _auth_headers("phase11-slack@example.com")
    _onboard(headers)
    _upload_resume(headers)
    _ingest_phase11_jobs()

    prefs = client.put(
        "/api/platform/slack/preferences",
        headers=headers,
        json={"enabled": True, "min_score": 60, "cooldown_minutes": 1, "channel": "#alerts"},
    )
    assert prefs.status_code == 200
    assert prefs.json()["enabled"] is True

    notification_prefs = client.put(
        "/api/notifications/preferences",
        headers=headers,
        json={
            "channels": ["in_app"],
            "enabled_triggers": ["high_match"],
            "quiet_hours": {"start": 1, "end": 2},
            "min_match_score": 60,
        },
    )
    assert notification_prefs.status_code == 200

    dispatch = dispatch_notifications_incremental()
    assert dispatch["queued_notifications"] >= 1

    events = client.get("/api/platform/slack/events", headers=headers)
    assert events.status_code == 200
    assert events.json()["total"] >= 1

    test_alert = client.post("/api/platform/slack/alerts/test", headers=headers, json={"score": 95})
    assert test_alert.status_code == 202
    assert "queued" in test_alert.json()


def test_phase11_referral_credit_awarded_on_paid_conversion() -> None:
    referrer_email = "phase11-referrer@example.com"
    referred_email = "phase11-referred@example.com"
    referrer_headers = _auth_headers(referrer_email)
    referred_headers = _auth_headers(referred_email)

    code_response = client.get("/api/platform/referrals/code", headers=referrer_headers)
    assert code_response.status_code == 200
    code = code_response.json()["code"]

    tracked = client.post(
        "/api/platform/referrals/track",
        headers=referred_headers,
        json={"referral_code": code, "referred_email": referred_email},
    )
    assert tracked.status_code == 201
    assert tracked.json()["status"] == "signed_up"

    apply_webhook_event(
        json.dumps(
            {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_phase11_referral_paid",
                        "customer_email": referred_email,
                        "customer": "cus_phase11_ref",
                        "subscription": "sub_phase11_ref",
                        "status": "active",
                        "plan": "pro",
                    }
                },
            }
        ).encode("utf-8")
    )

    summary = client.get("/api/platform/referrals/summary", headers=referrer_headers)
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["paid_conversions"] >= 1
    assert payload["credits"]["credits_available"] >= 1


def test_phase11_feature_flags_and_performance_cache() -> None:
    headers = _auth_headers("phase11-flags@example.com")
    _ingest_phase11_jobs()

    list_flags = client.get("/api/platform/feature-flags/admin", headers=headers)
    assert list_flags.status_code == 200
    assert len(list_flags.json()["items"]) >= 1

    updated = client.put(
        "/api/platform/feature-flags/admin",
        headers=headers,
        json={"name": "slack_alerts", "enabled": True, "rollout_percentage": 100},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "slack_alerts"

    override = client.put(
        "/api/platform/feature-flags/overrides",
        headers=headers,
        json={"name": "slack_alerts", "enabled": True},
    )
    assert override.status_code == 200
    assert override.json()["enabled"] is True

    first = client.get("/api/platform/performance/salary-benchmark?role=data engineer&location=austin", headers=headers)
    assert first.status_code == 200
    assert first.json()["cache"]["hit"] is False

    second = client.get("/api/platform/performance/salary-benchmark?role=data engineer&location=austin", headers=headers)
    assert second.status_code == 200
    assert second.json()["cache"]["hit"] is True

    controls = client.get("/api/platform/performance/queue-controls", headers=headers)
    assert controls.status_code == 200
    assert controls.json()["controls"]["queue_batch_size"] >= 1

