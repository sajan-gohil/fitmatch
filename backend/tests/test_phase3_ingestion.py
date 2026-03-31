from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from app.core.job_ingestion import (
    DEAD_LETTER_ITEMS,
    IngestionPipeline,
    ingest_with_retry,
    list_ingested_jobs,
    reset_ingestion_state,
    scrape_schedule,
)
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_ingestion_state()


def _auth_headers(email: str = "phase3@example.com") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "provider": "magic_link"})
    assert login.status_code == 202
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_ingestion_normalizes_and_deduplicates_jobs() -> None:
    pipeline = IngestionPipeline()
    payload = {
        "company": "FitMatch",
        "jobs": [
            {
                "id": "gh-1",
                "title": " Senior  Backend Engineer ",
                "location": {"name": " Toronto "},
                "content": "Build APIs",
                "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/1",
                "updated_at": "2026-03-31T20:00:00Z",
            },
            {
                "id": "gh-2",
                "title": "Senior Backend Engineer",
                "location": {"name": "Toronto"},
                "content": "Duplicate content",
                "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/2",
                "updated_at": "2026-03-31T20:00:00Z",
            },
        ],
    }

    result = pipeline.ingest("https://boards.greenhouse.io/fitmatch", payload)
    jobs = list_ingested_jobs()

    assert result["jobs_found"] == 2
    assert result["jobs_inserted"] == 1
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Senior Backend Engineer"
    assert jobs[0]["location"] == "Toronto"


def test_ingestion_retry_writes_dead_letter_on_failure() -> None:
    payload = {
        "company": "FitMatch",
        "jobs": [
            {
                "id": "gh-1",
                "title": "Data Engineer",
                "location": {"name": "Remote"},
                "content": "Test",
                "absolute_url": "https://boards.greenhouse.io/fitmatch/jobs/1",
                "updated_at": {"invalid": "date"},
            }
        ],
    }

    with pytest.raises(ValueError):
        ingest_with_retry("https://boards.greenhouse.io/fitmatch", payload, max_retries=2)

    assert len(DEAD_LETTER_ITEMS) == 1
    assert DEAD_LETTER_ITEMS[0]["ats"] == "greenhouse"


def test_job_api_exposes_ingested_results_and_trace() -> None:
    pipeline = IngestionPipeline()
    pipeline.ingest(
        "https://jobs.lever.co/fitmatch",
        {
            "company": "FitMatch",
            "postings": [
                {
                    "id": "lv-1",
                    "text": "Platform Engineer",
                    "categories": {"location": "Toronto, ON"},
                    "descriptionPlain": "Platform role",
                    "hostedUrl": "https://jobs.lever.co/fitmatch/lv-1",
                    "createdAt": 1711900800000,
                }
            ],
        },
    )

    headers = _auth_headers()
    list_response = client.get("/api/jobs", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["jobs"][0]["external_job_id"] == "lv-1"

    trace_response = client.get("/api/jobs/trace", headers=headers)
    assert trace_response.status_code == 200
    trace_payload = trace_response.json()
    assert len(trace_payload["runs"]) == 1
    assert len(trace_payload["raw_snapshots"]) == 1


def test_scrape_schedule_contains_phase3_ats_sources() -> None:
    sources = {item["name"] for item in scrape_schedule()}
    assert {
        "greenhouse_tier_1",
        "lever_tier_1",
        "workday_tier_2",
        "smartrecruiters_tier_2",
        "ashby_tier_2",
    }.issubset(sources)
