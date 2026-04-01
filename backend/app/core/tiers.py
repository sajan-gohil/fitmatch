from __future__ import annotations

from typing import Literal

Tier = Literal["free", "pro"]

FREE_MATCH_CAP = 5
FREE_LOCATION_CAP = 2


def get_user_tier(user_email: str) -> Tier:
    if user_email.strip().lower().endswith("+pro@fitmatch.dev"):
        return "pro"
    return "free"


def get_match_cap_for_tier(tier: Tier) -> int | None:
    if tier == "free":
        return FREE_MATCH_CAP
    return None


def get_location_cap_for_tier(tier: Tier) -> int | None:
    if tier == "free":
        return FREE_LOCATION_CAP
    return None
