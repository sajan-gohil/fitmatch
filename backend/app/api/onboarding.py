from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import AuthUser, get_current_user
from app.core.onboarding_store import get_user_preferences, save_user_preferences
from app.core.tiers import get_location_cap_for_tier, get_user_tier

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingRequest(BaseModel):
    target_roles: list[str] = Field(min_length=1)
    preferred_locations: list[str] = Field(min_length=1)
    work_type_preferences: list[str] = Field(min_length=1)


@router.post("", status_code=200)
def save_onboarding(
    payload: OnboardingRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    tier = get_user_tier(user.email)
    location_cap = get_location_cap_for_tier(tier)
    preferred_locations = payload.preferred_locations
    if location_cap is not None:
        preferred_locations = preferred_locations[:location_cap]

    normalized = {
        "target_roles": payload.target_roles,
        "preferred_locations": preferred_locations,
        "work_type_preferences": payload.work_type_preferences,
        "completed": True,
    }
    return save_user_preferences(user.email, normalized)


@router.get("", status_code=200)
def get_onboarding(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return get_user_preferences(user.email)
