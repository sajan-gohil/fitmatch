from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any
from uuid import uuid4

from app.core.phase10_growth import salary_benchmark_by_role_location
from app.core.settings import get_settings


@dataclass(frozen=True)
class SlackPreference:
    enabled: bool
    channel: str
    min_score: float
    cooldown_minutes: int


_phase11_lock = Lock()
_slack_preferences: dict[str, SlackPreference] = {}
_slack_events: list[dict[str, Any]] = []
_last_slack_event_at: dict[str, datetime] = {}
_feature_flags: dict[str, dict[str, Any]] = {
    "slack_alerts": {"enabled": True, "rollout_percentage": 100},
    "referrals": {"enabled": True, "rollout_percentage": 100},
    "pwa_mobile_shell": {"enabled": True, "rollout_percentage": 100},
    "phase11_perf_tuning": {"enabled": True, "rollout_percentage": 100},
}
_feature_flag_overrides: dict[str, dict[str, bool]] = {}
_referral_codes: dict[str, dict[str, Any]] = {}
_referrals_by_referrer: dict[str, list[dict[str, Any]]] = {}
_referral_credits: dict[str, dict[str, Any]] = {}
_salary_cache: dict[tuple[str | None, str | None], dict[str, Any]] = {}


def reset_phase11_state() -> None:
    with _phase11_lock:
        _slack_preferences.clear()
        _slack_events.clear()
        _last_slack_event_at.clear()
        _feature_flag_overrides.clear()
        _referral_codes.clear()
        _referrals_by_referrer.clear()
        _referral_credits.clear()
        _salary_cache.clear()


def _bounded_score(value: Any, default: float = 80.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(100.0, parsed))


def _bounded_percentage(value: Any, default: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(100, parsed))


def _to_positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, parsed)


def _stable_rollout_value(user_email: str, feature_name: str) -> int:
    seed = f"{user_email.strip().lower()}|{feature_name.strip().lower()}"
    return abs(hash(seed)) % 100


def get_feature_flag_state(user_email: str) -> dict[str, dict[str, bool | int]]:
    settings = get_settings()
    enabled = bool(settings.phase11_feature_flags_enabled)
    with _phase11_lock:
        user_overrides = _feature_flag_overrides.get(user_email.strip().lower(), {})
        response: dict[str, dict[str, bool | int]] = {}
        for flag_name, config in _feature_flags.items():
            base_enabled = bool(config.get("enabled", False)) and enabled
            rollout_percentage = _bounded_percentage(config.get("rollout_percentage"), default=100)
            in_rollout = _stable_rollout_value(user_email, flag_name) < rollout_percentage
            explicit_override = user_overrides.get(flag_name)
            is_enabled = (
                explicit_override
                if isinstance(explicit_override, bool)
                else (base_enabled and in_rollout)
            )
            response[flag_name] = {
                "enabled": is_enabled,
                "rollout_percentage": rollout_percentage,
            }
        return response


def list_feature_flags() -> list[dict[str, Any]]:
    with _phase11_lock:
        return [
            {
                "name": name,
                "enabled": bool(config.get("enabled", False)),
                "rollout_percentage": _bounded_percentage(config.get("rollout_percentage"), default=100),
            }
            for name, config in sorted(_feature_flags.items(), key=lambda item: item[0])
        ]


def update_feature_flag(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip().lower()
    if not name:
        raise ValueError("name is required")
    with _phase11_lock:
        if name not in _feature_flags:
            _feature_flags[name] = {"enabled": True, "rollout_percentage": 100}
        current = _feature_flags[name]
        if "enabled" in payload:
            current["enabled"] = bool(payload.get("enabled"))
        if "rollout_percentage" in payload:
            current["rollout_percentage"] = _bounded_percentage(payload.get("rollout_percentage"), default=100)
        return {
            "name": name,
            "enabled": bool(current.get("enabled", False)),
            "rollout_percentage": _bounded_percentage(current.get("rollout_percentage"), default=100),
        }


def set_feature_flag_override(user_email: str, payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("name") or "").strip().lower()
    if not name:
        raise ValueError("name is required")
    enabled_raw = payload.get("enabled")
    if not isinstance(enabled_raw, bool):
        raise ValueError("enabled must be a boolean")
    key = user_email.strip().lower()
    with _phase11_lock:
        overrides = _feature_flag_overrides.setdefault(key, {})
        overrides[name] = enabled_raw
        return {"user_email": key, "name": name, "enabled": enabled_raw}


def get_slack_preference(user_email: str) -> dict[str, Any]:
    key = user_email.strip().lower()
    with _phase11_lock:
        current = _slack_preferences.get(
            key,
            SlackPreference(enabled=False, channel="#fitmatch-alerts", min_score=85.0, cooldown_minutes=30),
        )
    return {
        "enabled": current.enabled,
        "channel": current.channel,
        "min_score": current.min_score,
        "cooldown_minutes": current.cooldown_minutes,
    }


def save_slack_preference(user_email: str, payload: dict[str, Any]) -> dict[str, Any]:
    current = get_slack_preference(user_email)
    next_preference = SlackPreference(
        enabled=bool(payload.get("enabled", current["enabled"])),
        channel=str(payload.get("channel") or current["channel"]).strip() or "#fitmatch-alerts",
        min_score=_bounded_score(payload.get("min_score"), default=float(current["min_score"])),
        cooldown_minutes=_to_positive_int(payload.get("cooldown_minutes"), int(current["cooldown_minutes"])),
    )
    with _phase11_lock:
        _slack_preferences[user_email.strip().lower()] = next_preference
    return get_slack_preference(user_email)


def queue_slack_alert(
    user_email: str,
    *,
    title: str,
    body: str,
    score: float | None = None,
    metadata: dict[str, Any] | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now = now_utc or datetime.now(UTC)
    key = user_email.strip().lower()
    flags = get_feature_flag_state(key)
    if not flags.get("slack_alerts", {}).get("enabled", False):
        return {"queued": False, "reason": "feature_disabled"}

    preference = get_slack_preference(key)
    if not preference["enabled"]:
        return {"queued": False, "reason": "opt_out"}
    if score is not None and float(score) < float(preference["min_score"]):
        return {"queued": False, "reason": "below_threshold"}

    cooldown_minutes = int(preference["cooldown_minutes"])
    with _phase11_lock:
        last_sent = _last_slack_event_at.get(key)
        if last_sent is not None and (now - last_sent) < timedelta(minutes=cooldown_minutes):
            return {"queued": False, "reason": "cooldown_active"}
        event = {
            "id": f"slack-{uuid4()}",
            "user_email": key,
            "channel": str(preference["channel"]),
            "title": title.strip(),
            "body": body.strip(),
            "score": float(score) if score is not None else None,
            "metadata": metadata or {},
            "created_at": now.isoformat(),
            "webhook_configured": bool(get_settings().slack_webhook_url),
        }
        _slack_events.append(event)
        _last_slack_event_at[key] = now
    return {"queued": True, "event_id": event["id"]}


def list_slack_events(user_email: str) -> list[dict[str, Any]]:
    key = user_email.strip().lower()
    with _phase11_lock:
        rows = [event for event in _slack_events if str(event.get("user_email")) == key]
    return sorted(rows, key=lambda item: str(item.get("created_at", "")), reverse=True)


def _ensure_referral_code(user_email: str) -> dict[str, Any]:
    key = user_email.strip().lower()
    existing = _referral_codes.get(key)
    if existing is not None:
        return existing
    digest = abs(hash(key)) % 1_000_000
    code = f"FM{digest:06d}"
    row = {
        "code": code,
        "referrer_email": key,
        "created_at": datetime.now(UTC).isoformat(),
    }
    _referral_codes[key] = row
    return row


def get_or_create_referral_code(user_email: str) -> dict[str, Any]:
    with _phase11_lock:
        row = _ensure_referral_code(user_email)
        return dict(row)


def track_referral_signup(*, referrer_email: str, referred_email: str) -> dict[str, Any]:
    referrer = referrer_email.strip().lower()
    referred = referred_email.strip().lower()
    if not referrer or not referred:
        raise ValueError("referrer_email and referred_email are required")
    if referrer == referred:
        raise ValueError("Self-referral is not allowed")
    flags = get_feature_flag_state(referrer)
    if not flags.get("referrals", {}).get("enabled", False):
        return {"tracked": False, "reason": "feature_disabled"}

    with _phase11_lock:
        rows = _referrals_by_referrer.setdefault(referrer, [])
        for row in rows:
            if row["referred_email"] == referred:
                return dict(row)
        created = {
            "id": f"ref-{uuid4()}",
            "referrer_email": referrer,
            "referred_email": referred,
            "status": "signed_up",
            "credit_granted": False,
            "credit_amount": 0,
            "created_at": datetime.now(UTC).isoformat(),
            "credited_at": None,
        }
        rows.append(created)
        return dict(created)


def track_referral_signup_by_code(*, referral_code: str, referred_email: str) -> dict[str, Any]:
    code = referral_code.strip().upper()
    if not code:
        raise ValueError("referral_code is required")
    with _phase11_lock:
        referrer_email = next(
            (
                row["referrer_email"]
                for row in _referral_codes.values()
                if str(row.get("code", "")).upper() == code
            ),
            None,
        )
    if not referrer_email:
        raise ValueError("Invalid referral_code")
    return track_referral_signup(referrer_email=referrer_email, referred_email=referred_email)


def apply_referral_credit_for_paid_plan(user_email: str) -> dict[str, Any]:
    paid_user = user_email.strip().lower()
    with _phase11_lock:
        source_referral: dict[str, Any] | None = None
        referrer_email: str | None = None
        for candidate_referrer, rows in _referrals_by_referrer.items():
            for row in rows:
                if row["referred_email"] == paid_user and not bool(row["credit_granted"]):
                    source_referral = row
                    referrer_email = candidate_referrer
                    break
            if source_referral is not None:
                break
        if source_referral is None or not referrer_email:
            return {"credited": False, "reason": "no_pending_referral"}

        source_referral["status"] = "paid_conversion"
        source_referral["credit_granted"] = True
        source_referral["credit_amount"] = 1
        source_referral["credited_at"] = datetime.now(UTC).isoformat()

        bucket = _referral_credits.setdefault(
            referrer_email,
            {
                "user_email": referrer_email,
                "credits_available": 0,
                "lifetime_credits": 0,
                "updated_at": datetime.now(UTC).isoformat(),
            },
        )
        bucket["credits_available"] = int(bucket.get("credits_available", 0)) + 1
        bucket["lifetime_credits"] = int(bucket.get("lifetime_credits", 0)) + 1
        bucket["updated_at"] = datetime.now(UTC).isoformat()
        return {
            "credited": True,
            "referrer_email": referrer_email,
            "referred_email": paid_user,
            "credits_available": bucket["credits_available"],
        }


def get_referral_summary(user_email: str) -> dict[str, Any]:
    key = user_email.strip().lower()
    with _phase11_lock:
        referrals = [dict(row) for row in _referrals_by_referrer.get(key, [])]
        credits = dict(
            _referral_credits.get(
                key,
                {
                    "user_email": key,
                    "credits_available": 0,
                    "lifetime_credits": 0,
                    "updated_at": None,
                },
            )
        )
    converted = len([row for row in referrals if bool(row.get("credit_granted"))])
    return {
        "code": get_or_create_referral_code(key)["code"],
        "referrals": referrals,
        "total_referrals": len(referrals),
        "paid_conversions": converted,
        "credits": credits,
    }


def get_salary_benchmark_cached(role: str | None = None, location: str | None = None) -> dict[str, Any]:
    role_key = role.strip().lower() if isinstance(role, str) and role.strip() else None
    location_key = location.strip().lower() if isinstance(location, str) and location.strip() else None
    cache_key = (role_key, location_key)
    ttl = max(1, get_settings().phase11_salary_cache_ttl_seconds)
    now = datetime.now(UTC)
    with _phase11_lock:
        cached = _salary_cache.get(cache_key)
        if cached is not None:
            expires_at = cached.get("expires_at")
            if isinstance(expires_at, datetime) and expires_at > now:
                return {
                    **cached["value"],
                    "cache": {"hit": True, "ttl_seconds": ttl},
                }
    value = salary_benchmark_by_role_location(role=role, location=location)
    with _phase11_lock:
        _salary_cache[cache_key] = {
            "value": value,
            "expires_at": now + timedelta(seconds=ttl),
        }
    return {
        **value,
        "cache": {"hit": False, "ttl_seconds": ttl},
    }


def get_queue_throughput_controls() -> dict[str, int]:
    settings = get_settings()
    return {
        "queue_batch_size": max(1, settings.phase11_queue_batch_size),
        "queue_partitions": max(1, settings.scrape_queue_partitions),
        "rate_limit_per_minute": max(1, settings.scrape_rate_limit_per_minute),
    }
