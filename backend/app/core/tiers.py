from __future__ import annotations

from typing import Literal

from app.core.billing import get_plan_for_user

Tier = Literal["free", "pro", "lifetime"]

FREE_MATCH_CAP = 5
FREE_LOCATION_CAP = 2


def get_user_tier(user_email: str) -> Tier:
    return get_plan_for_user(user_email.strip().lower())


def get_match_cap_for_tier(tier: Tier) -> int | None:
    if tier == "free":
        return FREE_MATCH_CAP
    return None


def get_location_cap_for_tier(tier: Tier) -> int | None:
    if tier == "free":
        return FREE_LOCATION_CAP
    return None


def can_access_match_detail(tier: Tier) -> bool:
    return tier in {"pro", "lifetime"}


def can_access_phase7_full_output(tier: Tier) -> bool:
    return tier in {"pro", "lifetime"}
