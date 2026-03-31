from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.core.job_ingestion import IngestionPipeline, reset_ingestion_state
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()


def _auth_headers(email: str = "phase4@example.com") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "provider": "magic_link"})
    assert login.status_code == 202
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _onboard(headers: dict[str, str], locations: list[str]) -> None:
    response = client.post(
        "/api/onboarding",
        headers=headers,
        json={
            "target_roles": ["Software Engineer"],
            "preferred_locations": locations,
            "work_type_preferences": ["remote"],
        },
    )
    assert response.status_code == 200


def _upload_resume(headers: dict[str, str], file_name: str = "resume.pdf") -> None:
    response = client.post(
        "/api/resume/upload",
        headers=headers,
        files={"file": (file_name, b"%PDF-1.4 phase4", "application/pdf")},
    )
    assert response.status_code == 201


def _ingest_jobs() -> None:
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://boards.greenhouse.io/fitmatch",
        {
            "company": "FitMatch",
            "jobs": [
                {
                    "id": "phase4-remote-1",
                    "title": "Software Engineer",
                    "location": {"name": "Toronto, ON"},
                    "content": "Build APIs using Python and SQL. Degree preferred.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase4-remote-1",
                    "updated_at": "2026-03-31T20:00:00Z",
                },
                {
                    "id": "phase4-remote-2",
                    "title": "Staff Platform Engineer",
                    "location": {"name": "Toronto, ON"},
                    "content": "Scale platform systems. Degree required. Golang preferred.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase4-remote-2",
                    "updated_at": "2026-03-31T19:00:00Z",
                },
                {
                    "id": "phase4-other-location",
                    "title": "Software Engineer",
                    "location": {"name": "New York, NY"},
                    "content": "Python and SQL role. Degree preferred.",
                    "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/phase4-other-location",
                    "updated_at": "2026-03-31T18:00:00Z",
                },
            ],
        },
    )


def test_matches_endpoint_requires_auth() -> None:
    response = client.get("/api/matches")
    assert response.status_code == 401


def test_matches_returns_ranked_top_n_with_breakdown() -> None:
    headers = _auth_headers("phase4-ranked@example.com")
    _onboard(headers, locations=["Toronto"])
    _upload_resume(headers)
    _ingest_jobs()

    response = client.get("/api/matches?limit=1", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    assert payload["total"] == 1
    assert len(payload["matches"]) == 1
    match = payload["matches"][0]
    assert set(match["breakdown"].keys()) == {"title", "skills", "experience", "education"}
    assert 0 <= match["score"] <= 100


def test_matches_enforces_locality_filter_before_ranking() -> None:
    headers = _auth_headers("phase4-location@example.com")
    _onboard(headers, locations=["Toronto"])
    _upload_resume(headers, file_name="data_resume.pdf")
    _ingest_jobs()

    response = client.get("/api/matches?limit=10", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    locations = [item["job"]["location"] for item in payload["matches"]]
    assert locations
    assert all("toronto" in location.lower() for location in locations)


def test_matches_sorted_by_score_descending() -> None:
    headers = _auth_headers("phase4-sorted@example.com")
    _onboard(headers, locations=["Toronto"])
    _upload_resume(headers)
    _ingest_jobs()

    response = client.get("/api/matches?limit=10", headers=headers)
    assert response.status_code == 200
    payload = response.json()

    scores = [item["score"] for item in payload["matches"]]
    assert scores == sorted(scores, reverse=True)
