from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.core.auth import AuthUser, get_current_user
from app.core.matching import list_top_matches_for_user

router = APIRouter(prefix="/matches", tags=["matches"])


class MatchResponse(BaseModel):
    job: dict[str, object]
    score: float
    breakdown: dict[str, float]


class MatchListResponse(BaseModel):
    matches: list[MatchResponse]
    total: int


@router.get("", response_model=MatchListResponse, status_code=status.HTTP_200_OK)
def get_matches(
    limit: int = Query(default=10, ge=1, le=50),
    user: AuthUser = Depends(get_current_user),
) -> MatchListResponse:
    matches = list_top_matches_for_user(user.email, limit=limit)
    return MatchListResponse(matches=matches, total=len(matches))
