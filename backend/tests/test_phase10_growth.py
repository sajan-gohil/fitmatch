from __future__ import annotations

import json

from fastapi.testclient import TestClient
import pytest

from app.core.billing import apply_webhook_event
from app.core.job_ingestion import IngestionPipeline, reset_ingestion_state
from app.core.lifetime_api import reset_lifetime_api_state
from app.core.phase10_growth import reset_growth_state
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()
    reset_growth_state()
    reset_lifetime_api_state()


def _auth_headers(email: str = "phase10@example.com") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "provider": "magic_link"})
    assert login.status_code == 202
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _ingest_phase10_jobs() -> None:
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://boards.greenhouse.io/fitmatch",
        {
            "company": "FitMatch",
            "jobs": [
                {
                    "id": "phase10-job-1",
                    "title": "Data Engineer",
                    "location": {"name": "Austin, TX"},
                    "content": "Build data products with Python and SQL.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase10-job-1",
                    "updated_at": "2026-04-01T08:00:00Z",
                    "salary_min": 120000,
                },
                {
                    "id": "phase10-job-2",
                    "title": "Senior Data Engineer",
                    "location": {"name": "Austin, TX"},
                    "content": "Lead data platform and modeling workflows.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase10-job-2",
                    "updated_at": "2026-04-01T08:05:00Z",
                    "salary_min": 140000,
                },
            ],
        },
    )


def _onboard_and_resume(headers: dict[str, str]) -> None:
    onboard = client.post(
        "/api/onboarding",
        headers=headers,
        json={
            "target_roles": ["Data Engineer"],
            "preferred_locations": ["Austin"],
            "work_type_preferences": ["remote"],
        },
    )
    assert onboard.status_code == 200
    resume = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": ("phase10_resume.pdf", b"%PDF-1.4 phase10", "application/pdf")},
    )
    assert resume.status_code == 201


def _upgrade_to_lifetime(email: str) -> None:
    apply_webhook_event(
        json.dumps(
            {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_phase10_lifetime",
                        "customer_email": email,
                        "customer": "cus_phase10",
                        "subscription": "sub_phase10",
                        "status": "active",
                        "plan": "lifetime",
                    }
                },
            }
        ).encode("utf-8")
    )


def test_phase10_watchlist_crud_and_application_tracker() -> None:
    headers = _auth_headers("phase10-growth@example.com")
    _ingest_phase10_jobs()

    watch = client.post("/api/growth/watchlist", headers=headers, json={"company_name": "FitMatch"})
    assert watch.status_code == 201
    watch_id = watch.json()["id"]

    watch_list = client.get("/api/growth/watchlist", headers=headers)
    assert watch_list.status_code == 200
    assert watch_list.json()["total"] == 1
    assert watch_list.json()["items"][0]["company_name"] == "FitMatch"

    app_upsert = client.put(
        "/api/growth/applications",
        headers=headers,
        json={
            "external_job_id": "phase10-job-1",
            "status": "applied",
            "notes": "Submitted via referral.",
        },
    )
    assert app_upsert.status_code == 200
    assert app_upsert.json()["status"] == "applied"
    app_id = app_upsert.json()["id"]

    apps = client.get("/api/growth/applications", headers=headers)
    assert apps.status_code == 200
    assert apps.json()["total"] == 1

    delete_app = client.delete(f"/api/growth/applications/{app_id}", headers=headers)
    assert delete_app.status_code == 200

    delete_watch = client.delete(f"/api/growth/watchlist/{watch_id}", headers=headers)
    assert delete_watch.status_code == 200


def test_phase10_salary_benchmark_and_scraper_controls() -> None:
    headers = _auth_headers("phase10-benchmark@example.com")
    _ingest_phase10_jobs()

    benchmark = client.get("/api/growth/salary-benchmark?role=data engineer&location=austin", headers=headers)
    assert benchmark.status_code == 200
    payload = benchmark.json()
    assert payload["count"] == 2
    assert payload["min_salary_min"] == 120000
    assert payload["max_salary_min"] == 140000

    controls = client.get("/api/growth/scraper-controls", headers=headers)
    assert controls.status_code == 200
    assert controls.json()["controls"]["rate_limit_per_minute"] >= 1
    assert controls.json()["controls"]["queue_partitions"] >= 1

    partition = client.get(
        "/api/growth/scraper-controls/partition",
        headers=headers,
        params={"source_url": "https://boards.greenhouse.io/fitmatch"},
    )
    assert partition.status_code == 200
    assert isinstance(partition.json()["partition"], int)


def test_phase10_lifetime_api_token_auth_and_quota() -> None:
    email = "phase10-lifetime@example.com"
    headers = _auth_headers(email)
    _onboard_and_resume(headers)
    _ingest_phase10_jobs()

    non_lifetime = client.post("/api/lifetime-api/tokens", headers=headers, json={"label": "cli"})
    assert non_lifetime.status_code == 403

    _upgrade_to_lifetime(email)
    created = client.post("/api/lifetime-api/tokens", headers=headers, json={"label": "cli"})
    assert created.status_code == 201
    raw_token = created.json()["token"]

    without_key = client.get("/api/lifetime-api/jobs")
    assert without_key.status_code == 401

    api_headers = {"X-FitMatch-API-Key": raw_token}
    jobs = client.get("/api/lifetime-api/jobs", headers=api_headers)
    assert jobs.status_code == 200
    assert jobs.json()["total"] >= 1

    matches = client.get("/api/lifetime-api/matches", headers=api_headers)
    assert matches.status_code == 200
    assert "quota_remaining" in matches.json()

    token_id = created.json()["token_id"]
    revoke = client.delete(f"/api/lifetime-api/tokens/{token_id}", headers=headers)
    assert revoke.status_code == 200

    revoked_use = client.get("/api/lifetime-api/jobs", headers=api_headers)
    assert revoked_use.status_code == 401
