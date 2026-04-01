from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.core.auth import AuthUser, get_current_user
from app.core.matching import list_top_matches_for_user
from app.core.tiers import get_match_cap_for_tier, get_user_tier

router = APIRouter(prefix="/matches", tags=["matches"])


class MatchResponse(BaseModel):
    job: dict[str, object]
    score: float
    breakdown: dict[str, float]


class MatchListResponse(BaseModel):
    matches: list[MatchResponse]
    total: int
    tier: str
    enforced_limit: int | None = None


@router.get("", response_model=MatchListResponse, status_code=status.HTTP_200_OK)
def get_matches(
    limit: int = Query(default=10, ge=1, le=50),
    user: AuthUser = Depends(get_current_user),
) -> MatchListResponse:
    tier = get_user_tier(user.email)
    cap = get_match_cap_for_tier(tier)
    effective_limit = min(limit, cap) if cap is not None else limit
    matches = list_top_matches_for_user(user.email, limit=effective_limit)
    return MatchListResponse(matches=matches, total=len(matches), tier=tier, enforced_limit=cap)
