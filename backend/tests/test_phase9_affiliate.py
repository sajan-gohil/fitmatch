from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.core.affiliate import reset_affiliate_state
from app.core.job_ingestion import IngestionPipeline, reset_ingestion_state
from app.core.notifications import reset_notification_state
from app.main import app
from app.worker import sync_affiliate_catalog

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()
    reset_notification_state()
    reset_affiliate_state()


def _auth_headers(email: str = "phase9@example.com") -> dict[str, str]:
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
        files={"file": ("data_resume.pdf", b"%PDF-1.4 phase9", "application/pdf")},
    )
    assert response.status_code == 201


def _ingest_phase9_job() -> None:
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://boards.greenhouse.io/fitmatch",
        {
            "company": "FitMatch",
            "jobs": [
                {
                    "id": "phase9-role-1",
                    "title": "Senior Data Engineer",
                    "location": {"name": "Toronto, ON"},
                    "content": "Build data products using Python, SQL, Airflow and dbt.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase9-role-1",
                    "updated_at": "2026-04-01T08:00:00Z",
                }
            ],
        },
    )


def test_phase9_resume_analysis_includes_course_recommendation_slots() -> None:
    headers = _auth_headers("phase9-analysis@example.com")
    _onboard(headers)
    _upload_resume(headers)
    _ingest_phase9_job()

    response = client.get("/api/resume-intelligence/jobs/phase9-role-1/analysis", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "course_recommendations" in payload
    placements = payload["course_recommendations"]
    assert "gap_report_courses" in placements
    assert "resume_score_courses" in placements
    assert "dashboard_skill_trends" in placements
    assert len(placements["gap_report_courses"]) >= 1


def test_phase9_affiliate_recommendations_and_event_tracking() -> None:
    headers = _auth_headers("phase9-events@example.com")
    sync_response = client.post(
        "/api/affiliate/catalog/sync",
        headers=headers,
        json={"skills": ["dbt", "python"], "force": True},
    )
    assert sync_response.status_code == 200
    assert sync_response.json()["course_count"] >= 2

    recs = client.get("/api/affiliate/recommendations?skills=dbt,python", headers=headers)
    assert recs.status_code == 200
    recommendations = recs.json()["recommendations"]
    assert len(recommendations) >= 1
    first_course = recommendations[0]["courses"][0]

    click = client.post(
        "/api/affiliate/events",
        headers=headers,
        json={
            "event_type": "click",
            "provider": first_course["provider"],
            "external_course_id": first_course["external_course_id"],
            "skill": recommendations[0]["skill"],
        },
    )
    assert click.status_code == 201
    assert click.json()["event_type"] == "click"

    conversion = client.post(
        "/api/affiliate/events",
        headers=headers,
        json={
            "event_type": "conversion",
            "provider": first_course["provider"],
            "external_course_id": first_course["external_course_id"],
            "skill": recommendations[0]["skill"],
        },
    )
    assert conversion.status_code == 201
    assert conversion.json()["event_type"] == "conversion"

    analytics = client.get("/api/affiliate/analytics", headers=headers)
    assert analytics.status_code == 200
    summary = analytics.json()
    assert summary["totals"]["impression"] >= 1
    assert summary["totals"]["click"] >= 1
    assert summary["totals"]["conversion"] >= 1


def test_phase9_admin_mappings_manual_and_ai_suggested() -> None:
    headers = _auth_headers("phase9-admin@example.com")
    _ = sync_affiliate_catalog(force=True)

    put = client.put(
        "/api/affiliate/admin/mappings",
        headers=headers,
        json={
            "skill": "airflow",
            "provider": "udemy",
            "external_course_id": "udemy-airflow-101",
            "source": "manual",
            "rationale": "Strong demand in ETL-heavy data engineering jobs.",
            "active": True,
        },
    )
    assert put.status_code == 200
    assert put.json()["skill"] == "airflow"

    suggest = client.post(
        "/api/affiliate/admin/mappings/suggest",
        headers=headers,
        json={"skills": ["airflow", "dbt"]},
    )
    assert suggest.status_code == 200
    suggestions = suggest.json()["suggestions"]
    assert len(suggestions) >= 1
    assert suggestions[0]["source"] == "ai_assisted"

    listing = client.get("/api/affiliate/admin/mappings", headers=headers)
    assert listing.status_code == 200
    assert any(item["skill"] == "airflow" for item in listing.json()["items"])
