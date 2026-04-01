from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.auth import AuthUser, get_current_user
from app.core.job_ingestion import list_ingested_jobs, list_ingestion_trace
from app.core.matching import compute_match_score
from app.core.resume_store import get_resumes_for_user

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobListResponse(BaseModel):
    jobs: list[dict[str, object]]
    total: int


@router.get("", response_model=JobListResponse, status_code=status.HTTP_200_OK)
def get_jobs(
    location: str | None = Query(default=None),
    user: AuthUser = Depends(get_current_user),
) -> JobListResponse:
    del user
    jobs = list_ingested_jobs()
    if location:
        normalized_location = location.strip().lower()
        jobs = [
            job
            for job in jobs
            if isinstance(job.get("location"), str)
            and normalized_location in str(job.get("location", "")).lower()
        ]
    return JobListResponse(jobs=jobs, total=len(jobs))


@router.get("/trace", status_code=status.HTTP_200_OK)
def get_ingestion_trace(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    del user
    return list_ingestion_trace()


@router.get("/{external_job_id}", status_code=status.HTTP_200_OK)
def get_job(external_job_id: str, user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    del user
    for job in list_ingested_jobs():
        if job.get("external_job_id") == external_job_id:
            return job

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.get("/{external_job_id}/match-detail", status_code=status.HTTP_200_OK)
def get_job_match_detail(external_job_id: str, user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    resume_list = get_resumes_for_user(user.email)
    if not resume_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    for job in list_ingested_jobs():
        if job.get("external_job_id") == external_job_id:
            score = compute_match_score(resume_list[-1], job)
            return {
                "job": job,
                "score": score.score,
                "breakdown": {
                    "title": score.title,
                    "skills": score.skills,
                    "experience": score.experience,
                    "education": score.education,
                },
            }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
