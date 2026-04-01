from __future__ import annotations

from typing import Any

_resumes: dict[str, dict[str, Any]] = {}


def save_resume(resume_id: str, document: dict[str, Any]) -> dict[str, Any]:
    _resumes[resume_id] = document
    return document


def get_resume(resume_id: str) -> dict[str, Any] | None:
    return _resumes.get(resume_id)


def get_resumes_for_user(user_email: str) -> list[dict[str, Any]]:
    return [resume for resume in _resumes.values() if resume.get("owner") == user_email]


def list_resume_owners() -> list[str]:
    owners = {resume.get("owner") for resume in _resumes.values() if isinstance(resume.get("owner"), str)}
    return sorted(owners)
