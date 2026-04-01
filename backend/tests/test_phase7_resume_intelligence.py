from __future__ import annotations

import json

from fastapi.testclient import TestClient
import pytest

from app.core.billing import apply_webhook_event
from app.core.job_ingestion import IngestionPipeline, reset_ingestion_state
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()


def _auth_headers(email: str = "phase7@example.com") -> dict[str, str]:
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


def _upload_resume(headers: dict[str, str], file_name: str = "data_resume.pdf") -> str:
    response = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": (file_name, b"%PDF-1.4 phase7", "application/pdf")},
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def _ingest_phase7_job() -> None:
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://boards.greenhouse.io/fitmatch",
        {
            "company": "FitMatch",
            "jobs": [
                {
                    "id": "phase7-role-1",
                    "title": "Senior Data Engineer",
                    "location": {"name": "Toronto, ON"},
                    "content": (
                        "Build data products using Python, SQL, Airflow and dbt. "
                        "Degree preferred and experience scaling pipelines."
                    ),
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase7-role-1",
                    "updated_at": "2026-04-01T08:00:00Z",
                }
            ],
        },
    )


def _upgrade_to_pro(email: str) -> None:
    apply_webhook_event(
        json.dumps(
            {
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_phase7_1",
                        "customer_email": email,
                        "customer": "cus_phase7_1",
                        "subscription": "sub_phase7_1",
                        "status": "active",
                        "plan": "pro",
                    }
                },
            }
        ).encode("utf-8")
    )


def test_phase7_analysis_returns_preview_for_free_tier() -> None:
    headers = _auth_headers("phase7-free@example.com")
    _onboard(headers)
    _upload_resume(headers)
    _ingest_phase7_job()

    response = client.get("/api/resume-intelligence/jobs/phase7-role-1/analysis", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["tier"] == "free"
    assert payload["is_preview"] is True
    assert len(payload["fit_report"]["suggestions"]) == 1
    assert len(payload["rewrite_suggestions"]) == 1
    assert "missing_skills" in payload["skill_gap"]


def test_phase7_analysis_returns_full_output_for_paid_tier() -> None:
    email = "phase7-paid@example.com"
    headers = _auth_headers(email)
    _onboard(headers)
    _upload_resume(headers)
    _ingest_phase7_job()
    _upgrade_to_pro(email)

    response = client.get("/api/resume-intelligence/jobs/phase7-role-1/analysis", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["tier"] == "pro"
    assert payload["is_preview"] is False
    assert len(payload["fit_report"]["suggestions"]) >= 1
    assert len(payload["rewrite_suggestions"]) >= 2
    assert "resume_scoring" in payload
    assert set(payload["resume_scoring"].keys()) == {
        "clarity_formatting",
        "quantification",
        "keyword_density",
        "experience_narrative",
        "skills_coverage",
        "overall",
    }


def test_phase7_rewrite_accept_edit_dismiss_flow() -> None:
    email = "phase7-rewrite@example.com"
    headers = _auth_headers(email)
    _onboard(headers)
    resume_id = _upload_resume(headers)
    _upgrade_to_pro(email)

    list_response = client.get(f"/api/resume-intelligence/resumes/{resume_id}/rewrites", headers=headers)
    assert list_response.status_code == 200
    suggestions = list_response.json()["rewrite_suggestions"]
    assert len(suggestions) >= 2
    first_id = suggestions[0]["id"]

    accept_response = client.post(
        f"/api/resume-intelligence/resumes/{resume_id}/rewrites/{first_id}",
        headers=headers,
        json={"action": "accept"},
    )
    assert accept_response.status_code == 200
    assert accept_response.json()["state"] == "accepted"

    second_id = suggestions[1]["id"]
    edit_response = client.post(
        f"/api/resume-intelligence/resumes/{resume_id}/rewrites/{second_id}",
        headers=headers,
        json={"action": "edit", "edited_text": "Improved rewritten bullet with measurable impact."},
    )
    assert edit_response.status_code == 200
    assert edit_response.json()["state"] == "edited"
    assert "measurable impact" in edit_response.json()["suggested"]

    dismiss_response = client.post(
        f"/api/resume-intelligence/resumes/{resume_id}/rewrites/{second_id}",
        headers=headers,
        json={"action": "dismiss"},
    )
    assert dismiss_response.status_code == 200
    assert dismiss_response.json()["state"] == "dismissed"
