from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _auth_headers(email: str = "user@example.com") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "provider": "magic_link"})
    assert login.status_code == 202
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_auth_callback_with_invalid_token_fails() -> None:
    response = client.post("/api/auth/callback", json={"token": "not-a-real-token"})

    assert response.status_code == 401


def test_onboarding_requires_auth() -> None:
    response = client.get("/api/onboarding")

    assert response.status_code == 401


def test_onboarding_round_trip() -> None:
    headers = _auth_headers()

    save = client.post(
        "/api/onboarding",
        headers=headers,
        json={
            "target_roles": ["Data Analyst"],
            "preferred_locations": ["Toronto"],
            "work_type_preferences": ["remote"],
        },
    )

    assert save.status_code == 200
    assert save.json()["completed"] is True

    fetch = client.get("/api/onboarding", headers=headers)
    assert fetch.status_code == 200
    assert fetch.json()["target_roles"] == ["Data Analyst"]


def test_resume_upload_and_fetch() -> None:
    headers = _auth_headers("resume-user@example.com")

    upload = client.post(
        "/api/resume/upload",
        headers=headers,
        files={
            "file": (
                "resume.pdf",
                b"%PDF-1.4 mock resume",
                "application/pdf",
            )
        },
    )

    assert upload.status_code == 201
    payload = upload.json()
    assert payload["parsed"]["format"] == "pdf"
    assert payload["parsed"]["skills"] == ["python", "sql"]

    resume_id = payload["id"]
    fetched = client.get(f"/api/resume/{resume_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == resume_id


def test_resume_upload_rejects_invalid_extension() -> None:
    headers = _auth_headers("invalid-ext@example.com")

    upload = client.post(
        "/api/resume/upload",
        headers=headers,
        files={
            "file": (
                "notes.txt",
                b"not a supported file",
                "text/plain",
            )
        },
    )

    assert upload.status_code == 400
