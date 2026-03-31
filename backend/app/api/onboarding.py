from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.auth import AuthUser, get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

_user_preferences: dict[str, dict[str, object]] = {}


class OnboardingRequest(BaseModel):
    target_roles: list[str] = Field(min_length=1)
    preferred_locations: list[str] = Field(min_length=1)
    work_type_preferences: list[str] = Field(min_length=1)


@router.post("", status_code=200)
def save_onboarding(
    payload: OnboardingRequest,
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    normalized = {
        "target_roles": payload.target_roles,
        "preferred_locations": payload.preferred_locations,
        "work_type_preferences": payload.work_type_preferences,
        "completed": True,
    }
    _user_preferences[user.email] = normalized
    return normalized


@router.get("", status_code=200)
def get_onboarding(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return _user_preferences.get(
        user.email,
        {
            "target_roles": [],
            "preferred_locations": [],
            "work_type_preferences": [],
            "completed": False,
        },
    )
