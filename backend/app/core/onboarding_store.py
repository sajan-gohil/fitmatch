from __future__ import annotations

from typing import Any

_user_preferences: dict[str, dict[str, Any]] = {}


def save_user_preferences(user_email: str, preferences: dict[str, Any]) -> dict[str, Any]:
    _user_preferences[user_email] = preferences
    return preferences


def get_user_preferences(user_email: str) -> dict[str, Any]:
    return _user_preferences.get(
        user_email,
        {
            "target_roles": [],
            "preferred_locations": [],
            "work_type_preferences": [],
            "completed": False,
        },
    )
