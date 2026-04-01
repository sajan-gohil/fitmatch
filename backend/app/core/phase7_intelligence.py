from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
import uuid
import re

from app.core.matching import MatchScore

QUALITY_DIMENSION_WEIGHTS: dict[str, float] = {
    "clarity_formatting": 0.20,
    "quantification": 0.20,
    "keyword_density": 0.20,
    "experience_narrative": 0.20,
    "skills_coverage": 0.20,
}

KNOWN_SKILLS: tuple[str, ...] = (
    "python",
    "sql",
    "airflow",
    "dbt",
    "aws",
    "gcp",
    "docker",
    "kubernetes",
    "fastapi",
    "react",
    "typescript",
    "golang",
    "java",
)

RewriteState = Literal["pending", "accepted", "dismissed", "edited"]
VALID_REWRITE_ACTIONS = {"accept", "dismiss", "edit"}


@dataclass(frozen=True)
class SkillGapResult:
    required_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]


@dataclass
class RewriteSuggestion:
    id: str
    resume_id: str
    original: str
    suggested: str
    state: RewriteState = "pending"


_rewrite_suggestions: dict[str, list[RewriteSuggestion]] = {}


def _normalize_score(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 2)


def extract_skill_gap(parsed_resume: dict[str, Any], job: dict[str, Any]) -> SkillGapResult:
    resume_skills = parsed_resume.get("skills", [])
    if not isinstance(resume_skills, list):
        resume_skills = []
    normalized_resume_skills = {
        str(skill).strip().lower() for skill in resume_skills if isinstance(skill, str) and str(skill).strip()
    }

    searchable = f"{job.get('title', '')} {job.get('description', '')}".lower()
    required = [skill for skill in KNOWN_SKILLS if skill in searchable]

    matched = [skill for skill in required if skill in normalized_resume_skills]
    missing = [skill for skill in required if skill not in normalized_resume_skills]
    return SkillGapResult(required_skills=required, matched_skills=matched, missing_skills=missing)


def _has_metrics_text(text: str) -> bool:
    return bool(re.search(r"\d", text))


def compute_resume_quality_scores(parsed_resume: dict[str, Any], job: dict[str, Any]) -> dict[str, float]:
    summary = str(parsed_resume.get("summary", "")).strip()
    target_role = str(parsed_resume.get("target_role", "")).strip()
    skills = parsed_resume.get("skills", [])
    if not isinstance(skills, list):
        skills = []
    normalized_skills = [str(skill).strip().lower() for skill in skills if isinstance(skill, str) and str(skill).strip()]

    job_text = " ".join([str(job.get("title", "")), str(job.get("description", ""))]).lower()
    clarity = _normalize_score(90.0 if summary else 65.0)
    quantification = _normalize_score(85.0 if _has_metrics_text(summary) else 60.0)
    keyword_hits = sum(1 for skill in normalized_skills if skill in job_text)
    keyword_density = _normalize_score((keyword_hits / max(len(normalized_skills), 1)) * 100.0)
    experience_narrative = _normalize_score(85.0 if target_role else 60.0)

    required = [skill for skill in KNOWN_SKILLS if skill in job_text]
    covered = sum(1 for skill in required if skill in normalized_skills)
    skills_coverage = _normalize_score((covered / max(len(required), 1)) * 100.0)

    weighted = (
        clarity * QUALITY_DIMENSION_WEIGHTS["clarity_formatting"]
        + quantification * QUALITY_DIMENSION_WEIGHTS["quantification"]
        + keyword_density * QUALITY_DIMENSION_WEIGHTS["keyword_density"]
        + experience_narrative * QUALITY_DIMENSION_WEIGHTS["experience_narrative"]
        + skills_coverage * QUALITY_DIMENSION_WEIGHTS["skills_coverage"]
    )
    return {
        "clarity_formatting": clarity,
        "quantification": quantification,
        "keyword_density": keyword_density,
        "experience_narrative": experience_narrative,
        "skills_coverage": skills_coverage,
        "overall": _normalize_score(weighted),
    }


def _title_case_skills(skills: list[str]) -> list[str]:
    return [skill.upper() if len(skill) <= 3 else skill.title() for skill in skills]


def generate_fit_report(
    parsed_resume: dict[str, Any],
    job: dict[str, Any],
    match_score: MatchScore,
) -> dict[str, Any]:
    gap = extract_skill_gap(parsed_resume, job)
    quality = compute_resume_quality_scores(parsed_resume, job)
    missing_display = _title_case_skills(gap.missing_skills)
    matched_display = _title_case_skills(gap.matched_skills)

    summary = (
        f"You match {match_score.score}% of this role. "
        f"Strong areas: {', '.join(matched_display) if matched_display else 'general alignment'}. "
        f"Missing skills to highlight or develop: {', '.join(missing_display) if missing_display else 'none detected'}."
    )

    suggestions: list[str] = []
    for missing in missing_display[:3]:
        suggestions.append(f"Add evidence of {missing} in your resume bullets with concrete outcomes.")
    if quality["quantification"] < 70:
        suggestions.append("Rewrite at least two bullets to include measurable impact (%, $, time saved, or throughput).")
    if quality["keyword_density"] < 70:
        suggestions.append("Align wording in your experience bullets with key terms from this job description.")

    if not suggestions:
        suggestions.append("Tailor your resume summary to mirror the role scope and domain language.")

    return {
        "skill_gap": {
            "required_skills": gap.required_skills,
            "matched_skills": gap.matched_skills,
            "missing_skills": gap.missing_skills,
        },
        "fit_report": {
            "summary": summary,
            "suggestions": suggestions[:5],
        },
        "resume_scoring": quality,
    }


def _default_rewrite_suggestions(parsed_resume: dict[str, Any], resume_id: str) -> list[RewriteSuggestion]:
    target_role = str(parsed_resume.get("target_role", "")).strip() or "your target role"
    return [
        RewriteSuggestion(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            original="Worked on backend services.",
            suggested=f"Built and shipped backend services for {target_role} workloads, improving API reliability and delivery speed.",
        ),
        RewriteSuggestion(
            id=str(uuid.uuid4()),
            resume_id=resume_id,
            original="Helped with data pipelines.",
            suggested="Designed and maintained data pipelines with clear ownership, reducing pipeline failures and improving freshness.",
        ),
    ]


def get_rewrite_suggestions(resume_id: str, parsed_resume: dict[str, Any]) -> list[dict[str, str]]:
    if resume_id not in _rewrite_suggestions:
        _rewrite_suggestions[resume_id] = _default_rewrite_suggestions(parsed_resume, resume_id)
    return [
        {
            "id": item.id,
            "resume_id": item.resume_id,
            "original": item.original,
            "suggested": item.suggested,
            "state": item.state,
        }
        for item in _rewrite_suggestions[resume_id]
    ]


def update_rewrite_suggestion(
    resume_id: str,
    suggestion_id: str,
    action: Literal["accept", "dismiss", "edit"],
    edited_text: str | None = None,
) -> dict[str, str] | None:
    items = _rewrite_suggestions.get(resume_id, [])
    for item in items:
        if item.id != suggestion_id:
            continue
        if action == "accept":
            item.state = "accepted"
        elif action == "dismiss":
            item.state = "dismissed"
        elif action == "edit":
            if edited_text is None or not edited_text.strip():
                return None
            item.suggested = edited_text.strip()
            item.state = "edited"
        else:
            return None
        return {
            "id": item.id,
            "resume_id": item.resume_id,
            "original": item.original,
            "suggested": item.suggested,
            "state": item.state,
        }
    return None


def apply_preview_gating(report: dict[str, Any], rewrite_suggestions: list[dict[str, str]], is_paid: bool) -> dict[str, Any]:
    if is_paid:
        return {
            **report,
            "rewrite_suggestions": rewrite_suggestions,
            "is_preview": False,
        }
    preview = {
        **report,
        "is_preview": True,
        "fit_report": {
            "summary": report["fit_report"]["summary"],
            "suggestions": report["fit_report"]["suggestions"][:1],
        },
        "skill_gap": {
            **report["skill_gap"],
            "missing_skills": report["skill_gap"]["missing_skills"][:2],
        },
        "rewrite_suggestions": rewrite_suggestions[:1],
    }
    return preview
