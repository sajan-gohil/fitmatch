from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any, Literal

from app.core.job_ingestion import list_ingested_jobs
from app.core.matching import list_top_matches_for_user
from app.core.onboarding_store import get_user_preferences
from app.core.resume_store import get_resumes_for_user
from app.core.settings import get_settings

NotificationChannel = Literal["email", "in_app", "sms"]
NotificationTrigger = Literal[
    "high_match",
    "watchlist",
    "salary_threshold",
    "freshness",
    "deadline",
]


@dataclass(frozen=True)
class NotificationPreference:
    channels: tuple[NotificationChannel, ...]
    enabled_triggers: tuple[NotificationTrigger, ...]
    quiet_hours_start: int
    quiet_hours_end: int
    min_match_score: float
    min_salary: int
    watchlist_companies: tuple[str, ...]


_notification_preferences: dict[str, NotificationPreference] = {}
_notifications_by_user: dict[str, list[dict[str, Any]]] = {}
_dispatched_event_keys: set[str] = set()
_notification_lock = Lock()
_email_outbox: list[dict[str, Any]] = []


def reset_notification_state() -> None:
    with _notification_lock:
        _notification_preferences.clear()
        _notifications_by_user.clear()
        _dispatched_event_keys.clear()
        _email_outbox.clear()


def _default_preference() -> NotificationPreference:
    settings = get_settings()
    return NotificationPreference(
        channels=("email", "in_app"),
        enabled_triggers=("high_match", "watchlist", "salary_threshold", "freshness", "deadline"),
        quiet_hours_start=21,
        quiet_hours_end=8,
        min_match_score=settings.notification_high_match_threshold,
        min_salary=settings.notification_default_min_salary,
        watchlist_companies=(),
    )


def _normalize_channels(value: Any) -> tuple[NotificationChannel, ...]:
    valid = {"email", "in_app", "sms"}
    if not isinstance(value, list):
        return _default_preference().channels
    channels = tuple(
        item for item in [str(raw).strip().lower() for raw in value] if item in valid
    )
    return channels or _default_preference().channels


def _normalize_triggers(value: Any) -> tuple[NotificationTrigger, ...]:
    valid = {"high_match", "watchlist", "salary_threshold", "freshness", "deadline"}
    if not isinstance(value, list):
        return _default_preference().enabled_triggers
    triggers = tuple(
        item for item in [str(raw).strip().lower() for raw in value] if item in valid
    )
    return triggers or _default_preference().enabled_triggers


def _to_hour(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, min(23, parsed))


def _to_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(100.0, parsed))


def _to_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, parsed)


def _normalize_watchlist(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items = [str(item).strip() for item in value if str(item).strip()]
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return tuple(ordered)


def get_notification_preferences(user_email: str) -> dict[str, Any]:
    preference = _notification_preferences.get(user_email, _default_preference())
    return {
        "channels": list(preference.channels),
        "enabled_triggers": list(preference.enabled_triggers),
        "quiet_hours": {
            "start": preference.quiet_hours_start,
            "end": preference.quiet_hours_end,
        },
        "min_match_score": preference.min_match_score,
        "min_salary": preference.min_salary,
        "watchlist_companies": list(preference.watchlist_companies),
    }


def save_notification_preferences(user_email: str, payload: dict[str, Any]) -> dict[str, Any]:
    current = _notification_preferences.get(user_email, _default_preference())
    updated = NotificationPreference(
        channels=_normalize_channels(payload.get("channels", list(current.channels))),
        enabled_triggers=_normalize_triggers(payload.get("enabled_triggers", list(current.enabled_triggers))),
        quiet_hours_start=_to_hour(payload.get("quiet_hours", {}).get("start") if isinstance(payload.get("quiet_hours"), dict) else None, current.quiet_hours_start),
        quiet_hours_end=_to_hour(payload.get("quiet_hours", {}).get("end") if isinstance(payload.get("quiet_hours"), dict) else None, current.quiet_hours_end),
        min_match_score=_to_float(payload.get("min_match_score"), current.min_match_score),
        min_salary=_to_int(payload.get("min_salary"), current.min_salary),
        watchlist_companies=_normalize_watchlist(payload.get("watchlist_companies", list(current.watchlist_companies))),
    )
    _notification_preferences[user_email] = updated
    return get_notification_preferences(user_email)


def list_notifications(user_email: str, unread_only: bool = False) -> list[dict[str, Any]]:
    items = _notifications_by_user.get(user_email, [])
    filtered = [item for item in items if (not unread_only or not item["read"])]
    return sorted(filtered, key=lambda item: item["created_at"], reverse=True)


def mark_notification_read(user_email: str, notification_id: str, read: bool) -> dict[str, Any] | None:
    items = _notifications_by_user.get(user_email, [])
    for item in items:
        if item["id"] != notification_id:
            continue
        item["read"] = read
        item["read_at"] = datetime.now(UTC).isoformat() if read else None
        return item
    return None


def _within_quiet_hours(preference: NotificationPreference, now_utc: datetime) -> bool:
    hour = now_utc.hour
    start = preference.quiet_hours_start
    end = preference.quiet_hours_end
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def _job_salary(job: dict[str, Any]) -> int:
    salary = job.get("salary_min")
    if isinstance(salary, (int, float)):
        return int(max(0, salary))
    return 0


def _job_deadline(job: dict[str, Any]) -> datetime | None:
    raw = job.get("application_deadline")
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _resume_is_stale(user_email: str, stale_days: int) -> bool:
    resumes = get_resumes_for_user(user_email)
    if not resumes:
        return False
    latest = resumes[-1]
    uploaded_at = latest.get("uploaded_at")
    if not isinstance(uploaded_at, str):
        return False
    text = uploaded_at
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        timestamp = datetime.fromisoformat(text)
    except ValueError:
        return False
    timestamp = timestamp.astimezone(UTC) if timestamp.tzinfo else timestamp.replace(tzinfo=UTC)
    age = datetime.now(UTC) - timestamp
    return age >= timedelta(days=stale_days)


def _event_key(user_email: str, trigger: NotificationTrigger, job_id: str) -> str:
    return f"{user_email}|{trigger}|{job_id}"


def _enqueue_notification(
    user_email: str,
    trigger: NotificationTrigger,
    title: str,
    body: str,
    channels: tuple[NotificationChannel, ...],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    notification = {
        "id": f"notif-{len(_notifications_by_user.get(user_email, [])) + 1}",
        "trigger": trigger,
        "title": title,
        "body": body,
        "channels": list(channels),
        "metadata": metadata,
        "read": False,
        "created_at": datetime.now(UTC).isoformat(),
        "read_at": None,
    }
    _notifications_by_user.setdefault(user_email, []).append(notification)
    if "email" in channels:
        _email_outbox.append(
            {
                "user_email": user_email,
                "subject": title,
                "html": f"<p>{body}</p>",
                "notification_id": notification["id"],
            }
        )
    return notification


def evaluate_notifications_for_user(user_email: str, *, now_utc: datetime | None = None) -> dict[str, Any]:
    now = now_utc or datetime.now(UTC)
    preference = _notification_preferences.get(user_email, _default_preference())
    if _within_quiet_hours(preference, now):
        return {"user_email": user_email, "queued": 0, "reason": "quiet_hours"}

    matches = list_top_matches_for_user(user_email, limit=25)
    onboarding = get_user_preferences(user_email)
    preferred_locations = onboarding.get("preferred_locations", [])
    if not isinstance(preferred_locations, list):
        preferred_locations = []

    queued = 0
    stale_days = get_settings().notification_resume_stale_days

    for match in matches:
        job = match.get("job", {}) if isinstance(match.get("job"), dict) else {}
        job_id = str(job.get("external_job_id") or "")
        if not job_id:
            continue

        score = float(match.get("score") or 0.0)
        company = str(job.get("company_name") or "Unknown company")
        title = str(job.get("title") or "New job match")
        salary = _job_salary(job)
        deadline = _job_deadline(job)

        if "high_match" in preference.enabled_triggers and score >= preference.min_match_score:
            key = _event_key(user_email, "high_match", job_id)
            if key not in _dispatched_event_keys:
                _enqueue_notification(
                    user_email,
                    "high_match",
                    f"High match: {title}",
                    f"{company} posted a new role matching {round(score, 2)}%.",
                    preference.channels,
                    {"external_job_id": job_id, "score": score},
                )
                _dispatched_event_keys.add(key)
                queued += 1

        if "watchlist" in preference.enabled_triggers and company:
            watch = {item.lower() for item in preference.watchlist_companies}
            if company.lower() in watch:
                key = _event_key(user_email, "watchlist", job_id)
                if key not in _dispatched_event_keys:
                    _enqueue_notification(
                        user_email,
                        "watchlist",
                        f"Watchlist update: {company}",
                        f"{company} posted {title}.",
                        preference.channels,
                        {"external_job_id": job_id, "company": company},
                    )
                    _dispatched_event_keys.add(key)
                    queued += 1

        if "salary_threshold" in preference.enabled_triggers and salary >= preference.min_salary > 0:
            key = _event_key(user_email, "salary_threshold", job_id)
            if key not in _dispatched_event_keys:
                _enqueue_notification(
                    user_email,
                    "salary_threshold",
                    f"Salary threshold met: {title}",
                    f"Estimated salary for {title} is ${salary:,}, above your threshold.",
                    preference.channels,
                    {"external_job_id": job_id, "salary_min": salary},
                )
                _dispatched_event_keys.add(key)
                queued += 1

        if "deadline" in preference.enabled_triggers and deadline is not None:
            days_until = (deadline - now).days
            if 0 <= days_until <= 3:
                key = _event_key(user_email, "deadline", job_id)
                if key not in _dispatched_event_keys:
                    _enqueue_notification(
                        user_email,
                        "deadline",
                        f"Deadline reminder: {title}",
                        f"Application deadline is on {deadline.date().isoformat()}.",
                        preference.channels,
                        {"external_job_id": job_id, "application_deadline": deadline.isoformat()},
                    )
                    _dispatched_event_keys.add(key)
                    queued += 1

        if preferred_locations and "freshness" in preference.enabled_triggers:
            key = _event_key(user_email, "freshness", job_id)
            if key not in _dispatched_event_keys:
                posted_at = str(job.get("posted_at") or "")
                if posted_at:
                    _enqueue_notification(
                        user_email,
                        "freshness",
                        f"Fresh posting: {title}",
                        f"A new role in your target market was added from {company}.",
                        preference.channels,
                        {"external_job_id": job_id, "posted_at": posted_at},
                    )
                    _dispatched_event_keys.add(key)
                    queued += 1

    if "freshness" in preference.enabled_triggers and _resume_is_stale(user_email, stale_days):
        key = _event_key(user_email, "freshness", "resume-stale")
        if key not in _dispatched_event_keys:
            _enqueue_notification(
                user_email,
                "freshness",
                "Resume freshness nudge",
                f"Your resume has not been updated in {stale_days}+ days. Refresh it to improve match quality.",
                preference.channels,
                {"stale_days": stale_days},
            )
            _dispatched_event_keys.add(key)
            queued += 1

    return {"user_email": user_email, "queued": queued, "reason": "evaluated"}


def render_weekly_digest_email(user_email: str, *, limit: int = 5) -> dict[str, str]:
    matches = list_top_matches_for_user(user_email, limit=limit)
    lines: list[str] = []
    for item in matches:
        job = item.get("job", {}) if isinstance(item.get("job"), dict) else {}
        lines.append(
            f"<li><strong>{job.get('title', 'Role')}</strong> — {job.get('company_name', 'Company')} "
            f"({item.get('score', 0)}%)</li>"
        )

    body_list = "".join(lines) if lines else "<li>No new matches this week.</li>"
    html = (
        "<h2>Your weekly FitMatch digest</h2>"
        "<p>Here are your top personalized roles this week:</p>"
        f"<ul>{body_list}</ul>"
    )
    text = (
        "Your weekly FitMatch digest\n"
        + "\n".join(
            [
                f"- {item.get('job', {}).get('title', 'Role')} at {item.get('job', {}).get('company_name', 'Company')} ({item.get('score', 0)}%)"
                for item in matches
            ]
        )
    )
    return {"subject": "Your weekly FitMatch digest", "html": html, "text": text}


def run_weekly_digest(now_utc: datetime | None = None) -> dict[str, Any]:
    now = now_utc or datetime.now(UTC)
    settings = get_settings()
    if now.weekday() != settings.notification_digest_weekday or now.hour != settings.notification_digest_hour_utc:
        return {"sent": 0, "reason": "outside_schedule"}

    sent = 0
    for user_email in _notification_preferences.keys():
        digest = render_weekly_digest_email(user_email)
        _email_outbox.append(
            {
                "user_email": user_email,
                "subject": digest["subject"],
                "html": digest["html"],
                "notification_id": None,
            }
        )
        sent += 1
    return {"sent": sent, "reason": "scheduled"}


def get_email_outbox() -> list[dict[str, Any]]:
    return list(_email_outbox)


def all_notification_users() -> list[str]:
    users = set(_notification_preferences.keys())
    users.update(_notifications_by_user.keys())
    for job in list_ingested_jobs():
        del job
    return sorted(users)
