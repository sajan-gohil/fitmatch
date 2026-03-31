from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.embeddings import cosine_similarity, generate_embedding
from app.core.job_ingestion import list_ingested_jobs
from app.core.onboarding_store import get_user_preferences
from app.core.resume_store import get_resumes_for_user

TITLE_WEIGHT = 0.30
SKILLS_WEIGHT = 0.40
EXPERIENCE_WEIGHT = 0.20
EDUCATION_WEIGHT = 0.10


@dataclass(frozen=True)
class MatchScore:
    score: float
    title: float
    skills: float
    experience: float
    education: float


def _normalize_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def compute_match_score(resume: dict[str, Any], job: dict[str, Any]) -> MatchScore:
    parsed = resume.get("parsed", {}) if isinstance(resume.get("parsed"), dict) else {}
    resume_target_role = str(parsed.get("target_role", "")).strip()
    job_title = str(job.get("title", "")).strip()

    title_similarity = cosine_similarity(
        generate_embedding(resume_target_role),
        generate_embedding(job_title),
    )
    title_score = _normalize_score(((title_similarity + 1) / 2) * 100)

    resume_skills = parsed.get("skills", [])
    if not isinstance(resume_skills, list):
        resume_skills = []
    job_description = str(job.get("description", "")).lower()
    matched_skill_count = sum(
        1
        for skill in resume_skills
        if isinstance(skill, str) and skill.strip() and skill.strip().lower() in job_description
    )
    skills_score = _normalize_score((matched_skill_count / max(len(resume_skills), 1)) * 100)

    experience_score = 100.0
    if "senior" in job_title.lower() and "senior" not in resume_target_role.lower():
        experience_score = 60.0
    elif "staff" in job_title.lower() and "staff" not in resume_target_role.lower():
        experience_score = 50.0
    experience_score = _normalize_score(experience_score)

    education_score = 100.0 if "degree" in job_description else 70.0
    education_score = _normalize_score(education_score)

    weighted = (
        title_score * TITLE_WEIGHT
        + skills_score * SKILLS_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + education_score * EDUCATION_WEIGHT
    )

    return MatchScore(
        score=_normalize_score(weighted),
        title=title_score,
        skills=skills_score,
        experience=experience_score,
        education=education_score,
    )


def _location_allowed(job_location: str | None, preferred_locations: list[str]) -> bool:
    if not preferred_locations:
        return True
    if not isinstance(job_location, str):
        return False
    normalized = job_location.strip().lower()
    return any(location.strip().lower() in normalized for location in preferred_locations if location.strip())


def _get_latest_resume(user_email: str) -> dict[str, Any] | None:
    resumes = get_resumes_for_user(user_email)
    if not resumes:
        return None
    return resumes[-1]


def list_top_matches_for_user(user_email: str, limit: int) -> list[dict[str, Any]]:
    preferences = get_user_preferences(user_email)
    preferred_locations = preferences.get("preferred_locations", [])
    if not isinstance(preferred_locations, list):
        preferred_locations = []

    resume = _get_latest_resume(user_email)
    if resume is None:
        return []

    results: list[dict[str, Any]] = []
    for job in list_ingested_jobs():
        if not _location_allowed(job.get("location"), preferred_locations):
            continue
        score = compute_match_score(resume, job)
        results.append(
            {
                "job": job,
                "score": score.score,
                "breakdown": {
                    "title": score.title,
                    "skills": score.skills,
                    "experience": score.experience,
                    "education": score.education,
                },
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]
