from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from threading import Lock
from typing import Any, Literal
from uuid import uuid4

from app.core.job_ingestion import list_ingested_jobs
from app.core.settings import get_settings

ApplicationStatus = Literal["saved", "applied", "interviewing", "offer", "rejected"]


@dataclass(frozen=True)
class WatchlistCompany:
    id: str
    user_email: str
    company_name: str
    created_at: str


@dataclass(frozen=True)
class ApplicationEntry:
    id: str
    user_email: str
    external_job_id: str
    company_name: str
    title: str
    status: ApplicationStatus
    applied_at: str | None
    notes: str
    created_at: str
    updated_at: str


_growth_lock = Lock()
_watchlists: dict[str, list[WatchlistCompany]] = {}
_applications: dict[str, list[ApplicationEntry]] = {}
_scrape_tokens_by_minute: dict[str, int] = {}


def reset_growth_state() -> None:
    with _growth_lock:
        _watchlists.clear()
        _applications.clear()
        _scrape_tokens_by_minute.clear()


def list_watchlist_companies(user_email: str) -> list[dict[str, str]]:
    with _growth_lock:
        rows = list(_watchlists.get(user_email, []))
    return [
        {
            "id": item.id,
            "company_name": item.company_name,
            "created_at": item.created_at,
        }
        for item in sorted(rows, key=lambda row: row.created_at, reverse=True)
    ]


def add_watchlist_company(user_email: str, company_name: str) -> dict[str, str]:
    normalized = company_name.strip()
    if not normalized:
        raise ValueError("company_name is required")
    with _growth_lock:
        current = _watchlists.setdefault(user_email, [])
        if any(item.company_name.lower() == normalized.lower() for item in current):
            return {
                "id": next(item.id for item in current if item.company_name.lower() == normalized.lower()),
                "company_name": next(item.company_name for item in current if item.company_name.lower() == normalized.lower()),
                "created_at": next(item.created_at for item in current if item.company_name.lower() == normalized.lower()),
            }
        item = WatchlistCompany(
            id=f"watch-{uuid4()}",
            user_email=user_email,
            company_name=normalized,
            created_at=datetime.now(UTC).isoformat(),
        )
        current.append(item)
        return {
            "id": item.id,
            "company_name": item.company_name,
            "created_at": item.created_at,
        }


def remove_watchlist_company(user_email: str, watchlist_id: str) -> bool:
    with _growth_lock:
        current = _watchlists.get(user_email, [])
        retained = [item for item in current if item.id != watchlist_id]
        deleted = len(retained) != len(current)
        _watchlists[user_email] = retained
    return deleted


def _normalize_status(value: str) -> ApplicationStatus:
    normalized = value.strip().lower()
    valid: set[str] = {"saved", "applied", "interviewing", "offer", "rejected"}
    if normalized not in valid:
        raise ValueError("Invalid application status")
    return normalized  # type: ignore[return-value]


def _find_job(external_job_id: str) -> dict[str, Any] | None:
    for job in list_ingested_jobs():
        if str(job.get("external_job_id") or "") == external_job_id:
            return job
    return None


def list_application_entries(user_email: str) -> list[dict[str, object]]:
    with _growth_lock:
        rows = list(_applications.get(user_email, []))
    rows_sorted = sorted(rows, key=lambda row: row.updated_at, reverse=True)
    return [
        {
            "id": item.id,
            "external_job_id": item.external_job_id,
            "company_name": item.company_name,
            "title": item.title,
            "status": item.status,
            "applied_at": item.applied_at,
            "notes": item.notes,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
        for item in rows_sorted
    ]


def upsert_application_entry(
    user_email: str,
    *,
    external_job_id: str,
    status: str,
    notes: str = "",
    applied_at: str | None = None,
) -> dict[str, object]:
    job = _find_job(external_job_id)
    if job is None:
        raise ValueError("Job not found")
    status_normalized = _normalize_status(status)
    if applied_at is not None and applied_at.strip():
        date.fromisoformat(applied_at.strip())
        applied_date = applied_at.strip()
    else:
        applied_date = datetime.now(UTC).date().isoformat() if status_normalized in {"applied", "interviewing", "offer"} else None

    with _growth_lock:
        rows = _applications.setdefault(user_email, [])
        now = datetime.now(UTC).isoformat()
        for index, item in enumerate(rows):
            if item.external_job_id != external_job_id:
                continue
            updated = ApplicationEntry(
                id=item.id,
                user_email=user_email,
                external_job_id=external_job_id,
                company_name=str(job.get("company_name") or item.company_name),
                title=str(job.get("title") or item.title),
                status=status_normalized,
                applied_at=applied_date,
                notes=notes.strip(),
                created_at=item.created_at,
                updated_at=now,
            )
            rows[index] = updated
            return {
                "id": updated.id,
                "external_job_id": updated.external_job_id,
                "company_name": updated.company_name,
                "title": updated.title,
                "status": updated.status,
                "applied_at": updated.applied_at,
                "notes": updated.notes,
                "created_at": updated.created_at,
                "updated_at": updated.updated_at,
            }
        created = ApplicationEntry(
            id=f"app-{uuid4()}",
            user_email=user_email,
            external_job_id=external_job_id,
            company_name=str(job.get("company_name") or "Unknown company"),
            title=str(job.get("title") or "Unknown role"),
            status=status_normalized,
            applied_at=applied_date,
            notes=notes.strip(),
            created_at=now,
            updated_at=now,
        )
        rows.append(created)
        return {
            "id": created.id,
            "external_job_id": created.external_job_id,
            "company_name": created.company_name,
            "title": created.title,
            "status": created.status,
            "applied_at": created.applied_at,
            "notes": created.notes,
            "created_at": created.created_at,
            "updated_at": created.updated_at,
        }


def delete_application_entry(user_email: str, application_id: str) -> bool:
    with _growth_lock:
        rows = _applications.get(user_email, [])
        retained = [item for item in rows if item.id != application_id]
        deleted = len(retained) != len(rows)
        _applications[user_email] = retained
    return deleted


def salary_benchmark_by_role_location(role: str | None = None, location: str | None = None) -> dict[str, object]:
    jobs = list_ingested_jobs()
    role_norm = role.strip().lower() if isinstance(role, str) and role.strip() else None
    location_norm = location.strip().lower() if isinstance(location, str) and location.strip() else None

    salary_rows: list[dict[str, object]] = []
    for job in jobs:
        salary = job.get("salary_min")
        title = str(job.get("title") or "")
        city = str(job.get("location") or "")
        if not isinstance(salary, (int, float)):
            continue
        if role_norm and role_norm not in title.lower():
            continue
        if location_norm and location_norm not in city.lower():
            continue
        salary_rows.append(
            {
                "external_job_id": str(job.get("external_job_id") or ""),
                "title": title,
                "location": city,
                "salary_min": int(salary),
            }
        )

    values = sorted(int(row["salary_min"]) for row in salary_rows)
    count = len(values)
    if count == 0:
        return {
            "count": 0,
            "median_salary_min": None,
            "average_salary_min": None,
            "p25_salary_min": None,
            "p75_salary_min": None,
            "min_salary_min": None,
            "max_salary_min": None,
            "samples": [],
        }

    def _percentile(percent: float) -> int:
        index = int((count - 1) * percent)
        return values[index]

    avg = round(sum(values) / count)
    return {
        "count": count,
        "median_salary_min": values[count // 2],
        "average_salary_min": avg,
        "p25_salary_min": _percentile(0.25),
        "p75_salary_min": _percentile(0.75),
        "min_salary_min": values[0],
        "max_salary_min": values[-1],
        "samples": salary_rows[:20],
    }


def get_scraper_scaling_controls() -> dict[str, int]:
    settings = get_settings()
    return {
        "rate_limit_per_minute": max(1, settings.scrape_rate_limit_per_minute),
        "queue_partitions": max(1, settings.scrape_queue_partitions),
    }


def evaluate_scrape_rate_limit(*, source_url: str, now_utc: datetime | None = None) -> dict[str, object]:
    del source_url
    controls = get_scraper_scaling_controls()
    now = now_utc or datetime.now(UTC)
    minute_bucket = now.strftime("%Y-%m-%dT%H:%M")
    limit = int(controls["rate_limit_per_minute"])

    with _growth_lock:
        used = _scrape_tokens_by_minute.get(minute_bucket, 0)
        if used >= limit:
            return {
                "allowed": False,
                "reason": "rate_limited",
                "bucket": minute_bucket,
                "remaining": 0,
            }
        used += 1
        _scrape_tokens_by_minute[minute_bucket] = used
        return {
            "allowed": True,
            "reason": "accepted",
            "bucket": minute_bucket,
            "remaining": max(0, limit - used),
        }


def queue_partition_for_source(source_url: str) -> int:
    controls = get_scraper_scaling_controls()
    partitions = int(controls["queue_partitions"])
    return abs(hash(source_url)) % partitions
