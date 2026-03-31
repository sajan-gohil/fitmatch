from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
from typing import Any
from urllib.parse import urljoin

from app.core.embeddings import generate_embedding

@dataclass(frozen=True)
class CanonicalJob:
    external_job_id: str
    company_name: str
    title: str
    location: str | None
    description: str
    apply_url: str
    posted_at: datetime | None
    ats: str
    source_url: str


class BaseATSAdapter:
    ats: str

    def can_handle(self, source_url: str) -> bool:
        raise NotImplementedError

    def parse(self, source_url: str, payload: dict[str, Any]) -> list[CanonicalJob]:
        raise NotImplementedError


class GreenhouseAdapter(BaseATSAdapter):
    ats = "greenhouse"

    def can_handle(self, source_url: str) -> bool:
        return "greenhouse" in source_url.lower()

    def parse(self, source_url: str, payload: dict[str, Any]) -> list[CanonicalJob]:
        company_name = str(payload.get("company") or "Unknown")
        jobs: list[CanonicalJob] = []
        for item in payload.get("jobs", []):
            jobs.append(
                CanonicalJob(
                    external_job_id=str(item["id"]),
                    company_name=company_name,
                    title=str(item.get("title") or "").strip(),
                    location=_clean_optional((item.get("location") or {}).get("name")),
                    description=str(item.get("content") or "").strip(),
                    apply_url=str(item.get("absolute_url") or "").strip(),
                    posted_at=_parse_datetime(item.get("updated_at")),
                    ats=self.ats,
                    source_url=source_url,
                )
            )
        return jobs


class LeverAdapter(BaseATSAdapter):
    ats = "lever"

    def can_handle(self, source_url: str) -> bool:
        return "lever.co" in source_url.lower()

    def parse(self, source_url: str, payload: dict[str, Any]) -> list[CanonicalJob]:
        company_name = str(payload.get("company") or "Unknown")
        jobs: list[CanonicalJob] = []
        for item in payload.get("postings", []):
            categories = item.get("categories") or {}
            jobs.append(
                CanonicalJob(
                    external_job_id=str(item["id"]),
                    company_name=company_name,
                    title=str(item.get("text") or "").strip(),
                    location=_clean_optional(categories.get("location")),
                    description=str(item.get("descriptionPlain") or "").strip(),
                    apply_url=str(item.get("hostedUrl") or "").strip(),
                    posted_at=_parse_datetime(item.get("createdAt")),
                    ats=self.ats,
                    source_url=source_url,
                )
            )
        return jobs


class WorkdayAdapter(BaseATSAdapter):
    ats = "workday"

    def can_handle(self, source_url: str) -> bool:
        lowered = source_url.lower()
        return "workday" in lowered or "myworkdayjobs" in lowered

    def parse(self, source_url: str, payload: dict[str, Any]) -> list[CanonicalJob]:
        company_name = str(payload.get("company") or "Unknown")
        host = str(payload.get("host") or source_url)
        jobs: list[CanonicalJob] = []
        for item in payload.get("jobPostings", []):
            bullet_fields = item.get("bulletFields") or []
            location = bullet_fields[0] if bullet_fields else None
            external_path = str(item.get("externalPath") or "").strip()
            jobs.append(
                CanonicalJob(
                    external_job_id=str(item["id"]),
                    company_name=company_name,
                    title=str(item.get("title") or "").strip(),
                    location=_clean_optional(location),
                    description=str(item.get("jobDescription") or "").strip(),
                    apply_url=urljoin(host if host.endswith("/") else f"{host}/", external_path.lstrip("/")),
                    posted_at=_parse_datetime(item.get("postedOn")),
                    ats=self.ats,
                    source_url=source_url,
                )
            )
        return jobs


class SmartRecruitersAdapter(BaseATSAdapter):
    ats = "smartrecruiters"

    def can_handle(self, source_url: str) -> bool:
        return "smartrecruiters" in source_url.lower()

    def parse(self, source_url: str, payload: dict[str, Any]) -> list[CanonicalJob]:
        company_name = str(payload.get("company") or "Unknown")
        jobs: list[CanonicalJob] = []
        for item in payload.get("content", []):
            location_data = item.get("location") or {}
            location_parts = [
                str(location_data.get("city") or "").strip(),
                str(location_data.get("region") or "").strip(),
                str(location_data.get("country") or "").strip(),
            ]
            description = (
                (((item.get("jobAd") or {}).get("sections") or {}).get("jobDescription") or {}).get("text")
                or ""
            )
            jobs.append(
                CanonicalJob(
                    external_job_id=str(item["id"]),
                    company_name=company_name,
                    title=str(item.get("name") or "").strip(),
                    location=_clean_optional(", ".join(part for part in location_parts if part)
                    ),
                    description=str(description).strip(),
                    apply_url=str(item.get("ref") or "").strip(),
                    posted_at=_parse_datetime(item.get("releasedDate")),
                    ats=self.ats,
                    source_url=source_url,
                )
            )
        return jobs


class AshbyAdapter(BaseATSAdapter):
    ats = "ashby"

    def can_handle(self, source_url: str) -> bool:
        return "ashby" in source_url.lower()

    def parse(self, source_url: str, payload: dict[str, Any]) -> list[CanonicalJob]:
        company_name = str((payload.get("company") or {}).get("name") or "Unknown")
        jobs: list[CanonicalJob] = []
        for item in payload.get("jobs", []):
            jobs.append(
                CanonicalJob(
                    external_job_id=str(item["id"]),
                    company_name=company_name,
                    title=str(item.get("title") or "").strip(),
                    location=_clean_optional(item.get("location")),
                    description=str(item.get("description") or "").strip(),
                    apply_url=str(item.get("jobUrl") or "").strip(),
                    posted_at=_parse_datetime(item.get("publishedDate")),
                    ats=self.ats,
                    source_url=source_url,
                )
            )
        return jobs


ADAPTERS: tuple[BaseATSAdapter, ...] = (
    GreenhouseAdapter(),
    LeverAdapter(),
    WorkdayAdapter(),
    SmartRecruitersAdapter(),
    AshbyAdapter(),
)


def get_adapter_for_source(source_url: str) -> BaseATSAdapter:
    for adapter in ADAPTERS:
        if adapter.can_handle(source_url):
            return adapter
    raise ValueError(f"No ATS adapter found for source URL: {source_url}")


INGESTED_JOBS: dict[str, dict[str, Any]] = {}
RAW_SNAPSHOTS: list[dict[str, Any]] = []
DEAD_LETTER_ITEMS: list[dict[str, Any]] = []
SCRAPE_RUNS: list[dict[str, Any]] = []


def reset_ingestion_state() -> None:
    INGESTED_JOBS.clear()
    RAW_SNAPSHOTS.clear()
    DEAD_LETTER_ITEMS.clear()
    SCRAPE_RUNS.clear()


def add_dead_letter_item(source_url: str, ats: str, payload: dict[str, Any], error: str) -> dict[str, Any]:
    item = {
        "id": f"dlq-{len(DEAD_LETTER_ITEMS) + 1}",
        "source_url": source_url,
        "ats": ats,
        "payload": payload,
        "error": error,
        "created_at": datetime.now(UTC).isoformat(),
    }
    DEAD_LETTER_ITEMS.append(item)
    return item


class IngestionPipeline:
    def ingest(self, source_url: str, payload: dict[str, Any]) -> dict[str, Any]:
        adapter = get_adapter_for_source(source_url)
        run = {
            "id": f"run-{len(SCRAPE_RUNS) + 1}",
            "source_url": source_url,
            "ats": adapter.ats,
            "started_at": datetime.now(UTC).isoformat(),
            "status": "in_progress",
        }
        SCRAPE_RUNS.append(run)
        RAW_SNAPSHOTS.append(
            {
                "run_id": run["id"],
                "source_url": source_url,
                "ats": adapter.ats,
                "captured_at": datetime.now(UTC).isoformat(),
                "payload": payload,
            }
        )

        parsed_jobs = adapter.parse(source_url, payload)
        normalized_jobs = [self._normalize(job) for job in parsed_jobs]

        inserted = 0
        for job in normalized_jobs:
            dedup_key = self._dedup_key(job)
            if dedup_key in INGESTED_JOBS:
                continue
            INGESTED_JOBS[dedup_key] = {
                **asdict(job),
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                "dedup_key": dedup_key,
                "embedding": generate_embedding(
                    " ".join([job.title, job.description, job.company_name, job.location or ""])
                ),
            }
            inserted += 1

        run["status"] = "completed"
        run["completed_at"] = datetime.now(UTC).isoformat()
        run["jobs_found"] = len(parsed_jobs)
        run["jobs_inserted"] = inserted

        return {
            "run_id": run["id"],
            "ats": adapter.ats,
            "jobs_found": len(parsed_jobs),
            "jobs_inserted": inserted,
        }

    def _normalize(self, job: CanonicalJob) -> CanonicalJob:
        return CanonicalJob(
            external_job_id=job.external_job_id.strip(),
            company_name=_normalize_whitespace(job.company_name).strip(),
            title=_normalize_whitespace(job.title).strip(),
            location=_clean_optional(_normalize_whitespace(job.location) if job.location else None),
            description=job.description.strip(),
            apply_url=job.apply_url.strip(),
            posted_at=job.posted_at,
            ats=job.ats,
            source_url=job.source_url,
        )

    def _dedup_key(self, job: CanonicalJob) -> str:
        posted_date = job.posted_at.date().isoformat() if job.posted_at else ""
        raw_key = "|".join(
            [
                job.company_name.lower(),
                job.title.lower(),
                (job.location or "").lower(),
                posted_date,
            ]
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def list_ingested_jobs() -> list[dict[str, Any]]:
    jobs = list(INGESTED_JOBS.values())
    jobs.sort(key=lambda job: job.get("posted_at") or "", reverse=True)
    return jobs


def list_ingestion_trace() -> dict[str, Any]:
    return {
        "runs": SCRAPE_RUNS,
        "raw_snapshots": RAW_SNAPSHOTS,
        "dead_letter_items": DEAD_LETTER_ITEMS,
    }


def ingest_with_retry(
    source_url: str,
    payload: dict[str, Any],
    max_retries: int = 3,
) -> dict[str, Any]:
    pipeline = IngestionPipeline()
    attempts = 0
    while attempts < max_retries:
        attempts += 1
        try:
            result = pipeline.ingest(source_url, payload)
            result["attempts"] = attempts
            return result
        except Exception as exc:  # noqa: BLE001
            if attempts >= max_retries:
                adapter_name = "unknown"
                try:
                    adapter_name = get_adapter_for_source(source_url).ats
                except Exception:  # noqa: BLE001
                    adapter_name = "unknown"
                add_dead_letter_item(
                    source_url=source_url,
                    ats=adapter_name,
                    payload=payload,
                    error=str(exc),
                )
                raise

    raise RuntimeError("ingest_with_retry exhausted retries without result")


def scrape_schedule() -> tuple[dict[str, str], ...]:
    return (
        {
            "name": "greenhouse_tier_1",
            "source_url": "https://boards.greenhouse.io/fitmatch",
            "cadence": "every_6_hours",
        },
        {
            "name": "lever_tier_1",
            "source_url": "https://jobs.lever.co/fitmatch",
            "cadence": "every_6_hours",
        },
        {
            "name": "workday_tier_2",
            "source_url": "https://fitmatch.wd1.myworkdayjobs.com/careers",
            "cadence": "daily",
        },
        {
            "name": "smartrecruiters_tier_2",
            "source_url": "https://careers.smartrecruiters.com/FitMatch",
            "cadence": "daily",
        },
        {
            "name": "ashby_tier_2",
            "source_url": "https://jobs.ashbyhq.com/fitmatch",
            "cadence": "daily",
        },
    )


def next_retry_backoff_seconds(attempt: int) -> int:
    base = 30
    max_backoff = 15 * 60
    return min(max_backoff, base * (2 ** max(attempt - 1, 0)))


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = _normalize_whitespace(str(value)).strip()
    return cleaned or None


def _normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)

    if isinstance(value, (int, float)):
        epoch = float(value)
        if epoch > 10_000_000_000:
            epoch = epoch / 1000.0
        return datetime.fromtimestamp(epoch, tz=UTC)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None

        if text.isdigit():
            epoch = int(text)
            if epoch > 10_000_000_000:
                epoch = epoch / 1000.0
            return datetime.fromtimestamp(epoch, tz=UTC)

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        try:
            parsed = datetime.fromisoformat(text)
            return parsed.astimezone(UTC) if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            pass

    raise ValueError(f"Unsupported datetime value: {json.dumps(value, default=str)}")
