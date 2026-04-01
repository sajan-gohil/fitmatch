from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.core.auth import AuthUser
from app.core.job_ingestion import list_ingested_jobs
from app.core.lifetime_api import (
    ensure_lifetime_plan,
    get_lifetime_api_caller,
    issue_lifetime_api_token,
    list_lifetime_api_tokens,
    revoke_lifetime_api_token,
)
from app.core.matching import list_top_matches_for_user

router = APIRouter(prefix="/lifetime-api", tags=["lifetime-api"])


@router.get("/tokens", status_code=status.HTTP_200_OK)
def get_tokens(user: AuthUser = Depends(ensure_lifetime_plan)) -> dict[str, object]:
    items = list_lifetime_api_tokens(user.email)
    return {"items": items, "total": len(items)}


@router.post("/tokens", status_code=status.HTTP_201_CREATED)
def create_token(
    payload: dict[str, object] = Body(default={}),
    user: AuthUser = Depends(ensure_lifetime_plan),
) -> dict[str, object]:
    label = str(payload.get("label") or "").strip()
    token = issue_lifetime_api_token(user.email, label)
    return token


@router.delete("/tokens/{token_id}", status_code=status.HTTP_200_OK)
def delete_token(token_id: str, user: AuthUser = Depends(ensure_lifetime_plan)) -> dict[str, object]:
    deleted = revoke_lifetime_api_token(user.email, token_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    return {"deleted": True}


@router.get("/jobs", status_code=status.HTTP_200_OK)
def api_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    caller: dict[str, object] = Depends(get_lifetime_api_caller),
) -> dict[str, object]:
    del caller
    jobs = list_ingested_jobs()[:limit]
    return {"items": jobs, "total": len(jobs)}


@router.get("/matches", status_code=status.HTTP_200_OK)
def api_matches(
    limit: int = Query(default=10, ge=1, le=50),
    caller: dict[str, object] = Depends(get_lifetime_api_caller),
) -> dict[str, object]:
    owner = str(caller["owner_email"])
    matches = list_top_matches_for_user(owner, limit=limit)
    return {
        "items": matches,
        "total": len(matches),
        "quota_daily": caller["quota_daily"],
        "quota_used": caller["quota_used"],
        "quota_remaining": caller["quota_remaining"],
    }
