from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.core.auth import AuthUser, get_current_user
from app.core.job_ingestion import list_ingested_jobs
from app.core.matching import compute_match_score
from app.core.phase7_intelligence import (
    VALID_REWRITE_ACTIONS,
    apply_preview_gating,
    generate_fit_report,
    get_rewrite_suggestions,
    update_rewrite_suggestion,
)
from app.core.resume_store import get_resume, get_resumes_for_user
from app.core.tiers import can_access_phase7_full_output, get_user_tier

router = APIRouter(prefix="/resume-intelligence", tags=["resume-intelligence"])


def _get_job_or_404(external_job_id: str) -> dict[str, object]:
    for job in list_ingested_jobs():
        if job.get("external_job_id") == external_job_id:
            return job
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


def _get_resume_or_404(resume_id: str, user: AuthUser) -> dict[str, object]:
    resume = get_resume(resume_id)
    if resume is None or resume.get("owner") != user.email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.get("/jobs/{external_job_id}/analysis", status_code=status.HTTP_200_OK)
def get_job_resume_analysis(
    external_job_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    tier = get_user_tier(user.email)
    is_paid = can_access_phase7_full_output(tier)

    resumes = get_resumes_for_user(user.email)
    if not resumes:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    resume = resumes[-1]
    parsed = resume.get("parsed", {}) if isinstance(resume.get("parsed"), dict) else {}
    job = _get_job_or_404(external_job_id)
    score = compute_match_score(resume, job)
    report = generate_fit_report(parsed, job, score)
    rewrites = get_rewrite_suggestions(str(resume.get("id")), parsed)

    return {
        "tier": tier,
        **apply_preview_gating(report, rewrites, is_paid=is_paid),
    }


@router.get("/resumes/{resume_id}/rewrites", status_code=status.HTTP_200_OK)
def list_resume_rewrites(
    resume_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    resume = _get_resume_or_404(resume_id, user)
    parsed = resume.get("parsed", {}) if isinstance(resume.get("parsed"), dict) else {}
    tier = get_user_tier(user.email)
    is_paid = can_access_phase7_full_output(tier)
    rewrites = get_rewrite_suggestions(resume_id, parsed)
    return {
        "tier": tier,
        "is_preview": not is_paid,
        "rewrite_suggestions": rewrites if is_paid else rewrites[:1],
    }


@router.post("/resumes/{resume_id}/rewrites/{suggestion_id}", status_code=status.HTTP_200_OK)
def update_resume_rewrite_state(
    resume_id: str,
    suggestion_id: str,
    payload: dict[str, str] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    _get_resume_or_404(resume_id, user)
    action = payload.get("action")
    if not action or action not in VALID_REWRITE_ACTIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    updated = update_rewrite_suggestion(
        resume_id=resume_id,
        suggestion_id=suggestion_id,
        action=action,
        edited_text=payload.get("edited_text"),
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rewrite suggestion not found")
    return updated
