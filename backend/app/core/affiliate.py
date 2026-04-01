from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any, Literal, Protocol
from uuid import uuid4

from app.core.settings import get_settings

CourseProvider = Literal["udemy", "coursera"]
MappingSource = Literal["manual", "ai_assisted"]
AnalyticsEventType = Literal["impression", "click", "conversion"]


class CourseCatalogProviderAdapter(Protocol):
    provider: CourseProvider

    def fetch_catalog(self, skills: list[str]) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class SkillCourseMapping:
    skill: str
    provider: CourseProvider
    external_course_id: str
    source: MappingSource
    rationale: str
    active: bool = True


_affiliate_lock = Lock()
_provider_adapters: dict[CourseProvider, CourseCatalogProviderAdapter] = {}
_catalog_cache: list[dict[str, Any]] = []
_catalog_last_sync_at: datetime | None = None
_last_successful_catalog: list[dict[str, Any]] = []
_skill_course_mappings: dict[str, list[SkillCourseMapping]] = {}
_analytics_events: list[dict[str, Any]] = []


def _normalized_skill(value: str) -> str:
    return value.strip().lower()


def _display_skill(value: str) -> str:
    cleaned = value.strip().lower()
    if len(cleaned) <= 3:
        return cleaned.upper()
    return cleaned.title()


class UdemyCatalogAdapter:
    provider: CourseProvider = "udemy"

    def fetch_catalog(self, skills: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for skill in skills:
            normalized = _normalized_skill(skill)
            display = _display_skill(normalized)
            course_id = f"udemy-{normalized.replace(' ', '-')}-101"
            results.append(
                {
                    "provider": self.provider,
                    "external_course_id": course_id,
                    "skill": normalized,
                    "title": f"{display} Bootcamp for Job Seekers",
                    "description": f"Practical {display} projects and interview-ready outcomes.",
                    "rating": 4.5,
                    "price": "$14.99",
                    "enrollment_count": 25000,
                    "course_url": f"https://www.udemy.com/course/{course_id}/",
                    "affiliate_url": f"https://affiliate.fitmatch.dev/udemy/{course_id}",
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            )
        return results


class CourseraCatalogAdapter:
    provider: CourseProvider = "coursera"

    def fetch_catalog(self, skills: list[str]) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for skill in skills:
            normalized = _normalized_skill(skill)
            display = _display_skill(normalized)
            course_id = f"coursera-{normalized.replace(' ', '-')}-foundations"
            results.append(
                {
                    "provider": self.provider,
                    "external_course_id": course_id,
                    "skill": normalized,
                    "title": f"{display} Foundations Specialization",
                    "description": f"Guided path to build confidence with {display}.",
                    "rating": 4.6,
                    "price": "Free trial",
                    "enrollment_count": 100000,
                    "course_url": f"https://www.coursera.org/learn/{course_id}",
                    "affiliate_url": f"https://affiliate.fitmatch.dev/coursera/{course_id}",
                    "updated_at": datetime.now(UTC).isoformat(),
                }
            )
        return results


def _seed_defaults() -> None:
    if _provider_adapters:
        return
    register_provider_adapter(UdemyCatalogAdapter())
    register_provider_adapter(CourseraCatalogAdapter())

    default_entries = (
        SkillCourseMapping(
            skill="dbt",
            provider="coursera",
            external_course_id="coursera-dbt-foundations",
            source="manual",
            rationale="High-demand analytics engineering skill in data-role postings.",
        ),
        SkillCourseMapping(
            skill="python",
            provider="udemy",
            external_course_id="udemy-python-101",
            source="manual",
            rationale="Most requested language across backend and data roles.",
        ),
        SkillCourseMapping(
            skill="sql",
            provider="coursera",
            external_course_id="coursera-sql-foundations",
            source="manual",
            rationale="Core screening requirement in matching results.",
        ),
        SkillCourseMapping(
            skill="quantification",
            provider="udemy",
            external_course_id="udemy-quantification-101",
            source="manual",
            rationale="Improves measurable impact writing in resume bullets.",
        ),
    )
    for entry in default_entries:
        _skill_course_mappings.setdefault(entry.skill, []).append(entry)


def reset_affiliate_state() -> None:
    with _affiliate_lock:
        _provider_adapters.clear()
        _catalog_cache.clear()
        global _catalog_last_sync_at
        _catalog_last_sync_at = None
        _last_successful_catalog.clear()
        _skill_course_mappings.clear()
        _analytics_events.clear()
        _seed_defaults()


def register_provider_adapter(adapter: CourseCatalogProviderAdapter) -> None:
    _provider_adapters[adapter.provider] = adapter


def list_provider_adapters() -> list[str]:
    _seed_defaults()
    return sorted(_provider_adapters.keys())


def _is_cache_fresh() -> bool:
    if _catalog_last_sync_at is None:
        return False
    settings = get_settings()
    age = datetime.now(UTC) - _catalog_last_sync_at
    return age < timedelta(hours=max(1, settings.affiliate_catalog_sync_interval_hours))


def _collect_catalog(skills: list[str]) -> list[dict[str, Any]]:
    _seed_defaults()
    deduped_skills = sorted({_normalized_skill(skill) for skill in skills if _normalized_skill(skill)})
    if not deduped_skills:
        deduped_skills = sorted(_skill_course_mappings.keys())
    courses: list[dict[str, Any]] = []
    for adapter in _provider_adapters.values():
        courses.extend(adapter.fetch_catalog(deduped_skills))
    return courses


def sync_catalog(skills: list[str] | None = None, *, force: bool = False) -> dict[str, Any]:
    _seed_defaults()
    target_skills = skills if isinstance(skills, list) else []
    with _affiliate_lock:
        if not force and _catalog_cache and _is_cache_fresh():
            return {
                "synced": False,
                "used_cache": True,
                "used_stale_fallback": False,
                "course_count": len(_catalog_cache),
                "last_synced_at": _catalog_last_sync_at.isoformat() if _catalog_last_sync_at else None,
            }
        try:
            fresh = _collect_catalog(target_skills)
            _catalog_cache.clear()
            _catalog_cache.extend(fresh)
            _last_successful_catalog.clear()
            _last_successful_catalog.extend(fresh)
            global _catalog_last_sync_at
            _catalog_last_sync_at = datetime.now(UTC)
            return {
                "synced": True,
                "used_cache": False,
                "used_stale_fallback": False,
                "course_count": len(_catalog_cache),
                "last_synced_at": _catalog_last_sync_at.isoformat(),
            }
        except Exception:
            if _last_successful_catalog:
                _catalog_cache.clear()
                _catalog_cache.extend(_last_successful_catalog)
                return {
                    "synced": False,
                    "used_cache": False,
                    "used_stale_fallback": True,
                    "course_count": len(_catalog_cache),
                    "last_synced_at": _catalog_last_sync_at.isoformat() if _catalog_last_sync_at else None,
                }
            raise


def _catalog_for_skill(skill: str) -> list[dict[str, Any]]:
    normalized = _normalized_skill(skill)
    return [item for item in _catalog_cache if _normalized_skill(str(item.get("skill", ""))) == normalized]


def _find_catalog_item(provider: str, external_course_id: str) -> dict[str, Any] | None:
    provider_norm = provider.strip().lower()
    for item in _catalog_cache:
        if (
            str(item.get("provider", "")).strip().lower() == provider_norm
            and str(item.get("external_course_id", "")).strip() == external_course_id
        ):
            return item
    return None


def list_skill_course_mappings() -> list[dict[str, Any]]:
    _seed_defaults()
    rows: list[dict[str, Any]] = []
    for skill, entries in _skill_course_mappings.items():
        for entry in entries:
            rows.append(
                {
                    "skill": skill,
                    "provider": entry.provider,
                    "external_course_id": entry.external_course_id,
                    "source": entry.source,
                    "rationale": entry.rationale,
                    "active": entry.active,
                }
            )
    rows.sort(key=lambda row: (row["skill"], row["provider"], row["external_course_id"]))
    return rows


def upsert_skill_course_mapping(payload: dict[str, Any]) -> dict[str, Any]:
    _seed_defaults()
    skill = _normalized_skill(str(payload.get("skill", "")))
    provider = str(payload.get("provider", "")).strip().lower()
    external_course_id = str(payload.get("external_course_id", "")).strip()
    source_raw = str(payload.get("source", "manual")).strip().lower()
    source: MappingSource = "ai_assisted" if source_raw == "ai_assisted" else "manual"
    rationale = str(payload.get("rationale", "")).strip() or "Curated mapping."
    active = bool(payload.get("active", True))
    if not skill or provider not in {"udemy", "coursera"} or not external_course_id:
        raise ValueError("Invalid mapping payload")
    entries = _skill_course_mappings.setdefault(skill, [])
    for index, entry in enumerate(entries):
        if entry.provider == provider and entry.external_course_id == external_course_id:
            entries[index] = SkillCourseMapping(
                skill=skill,
                provider=provider,  # type: ignore[arg-type]
                external_course_id=external_course_id,
                source=source,
                rationale=rationale,
                active=active,
            )
            return {
                "skill": skill,
                "provider": provider,
                "external_course_id": external_course_id,
                "source": source,
                "rationale": rationale,
                "active": active,
            }
    entries.append(
        SkillCourseMapping(
            skill=skill,
            provider=provider,  # type: ignore[arg-type]
            external_course_id=external_course_id,
            source=source,
            rationale=rationale,
            active=active,
        )
    )
    return {
        "skill": skill,
        "provider": provider,
        "external_course_id": external_course_id,
        "source": source,
        "rationale": rationale,
        "active": active,
    }


def suggest_ai_skill_course_mappings(skills: list[str]) -> list[dict[str, Any]]:
    sync_catalog(skills=skills, force=False)
    suggestions: list[dict[str, Any]] = []
    for raw_skill in skills:
        skill = _normalized_skill(raw_skill)
        if not skill:
            continue
        options = _catalog_for_skill(skill)
        if not options:
            continue
        primary = sorted(
            options,
            key=lambda item: (
                float(item.get("rating", 0.0)),
                int(item.get("enrollment_count", 0)),
            ),
            reverse=True,
        )[0]
        suggestions.append(
            {
                "skill": skill,
                "provider": primary["provider"],
                "external_course_id": primary["external_course_id"],
                "source": "ai_assisted",
                "rationale": "Suggested from catalog relevance, rating, and enrollment strength.",
                "active": True,
            }
        )
    return suggestions


def _mapping_backed_courses(skill: str, limit: int) -> list[dict[str, Any]]:
    normalized = _normalized_skill(skill)
    entries = [entry for entry in _skill_course_mappings.get(normalized, []) if entry.active]
    rows: list[dict[str, Any]] = []
    for entry in entries:
        catalog_item = _find_catalog_item(entry.provider, entry.external_course_id)
        if catalog_item is None:
            continue
        rows.append(
            {
                **catalog_item,
                "mapping_source": entry.source,
                "mapping_rationale": entry.rationale,
            }
        )
    if rows:
        return rows[:limit]
    return _catalog_for_skill(normalized)[:limit]


def recommend_courses_for_skills(skills: list[str], *, per_skill_limit: int = 2) -> list[dict[str, Any]]:
    unique_skills = sorted({_normalized_skill(skill) for skill in skills if _normalized_skill(skill)})
    if not unique_skills:
        return []
    sync_catalog(skills=unique_skills, force=False)
    recommendations: list[dict[str, Any]] = []
    for skill in unique_skills:
        courses = _mapping_backed_courses(skill, limit=per_skill_limit)
        if not courses:
            continue
        recommendations.append({"skill": skill, "courses": courses})
    return recommendations


def build_contextual_course_placements(
    *,
    missing_skills: list[str],
    resume_scoring: dict[str, Any],
) -> dict[str, Any]:
    missing = [_normalized_skill(skill) for skill in missing_skills if _normalized_skill(skill)]
    gap_report_courses = recommend_courses_for_skills(missing, per_skill_limit=2)
    weak_dimensions = [
        key
        for key in ("quantification", "keyword_density", "skills_coverage", "clarity_formatting", "experience_narrative")
        if float(resume_scoring.get(key, 100.0)) < 70.0
    ]
    dimension_skills_map = {
        "quantification": "quantification",
        "keyword_density": "keyword optimization",
        "skills_coverage": "skills mapping",
        "clarity_formatting": "resume writing",
        "experience_narrative": "storytelling",
    }
    resume_score_courses: list[dict[str, Any]] = []
    for dimension in weak_dimensions:
        mapped_skill = dimension_skills_map[dimension]
        recs = recommend_courses_for_skills([mapped_skill], per_skill_limit=1)
        if not recs:
            continue
        resume_score_courses.append(
            {
                "dimension": dimension,
                "skill": mapped_skill,
                "course": recs[0]["courses"][0],
            }
        )

    dashboard_skill_trends = recommend_courses_for_skills(missing[:3], per_skill_limit=1)
    return {
        "gap_report_courses": gap_report_courses,
        "resume_score_courses": resume_score_courses,
        "dashboard_skill_trends": dashboard_skill_trends,
    }


def track_affiliate_event(
    *,
    user_email: str,
    event_type: AnalyticsEventType,
    provider: str,
    external_course_id: str,
    skill: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if event_type not in {"impression", "click", "conversion"}:
        raise ValueError("Invalid event type")
    event = {
        "id": f"affevt-{uuid4()}",
        "user_email": user_email.strip().lower(),
        "event_type": event_type,
        "provider": provider.strip().lower(),
        "external_course_id": external_course_id.strip(),
        "skill": _normalized_skill(skill) if isinstance(skill, str) and skill.strip() else None,
        "metadata": metadata or {},
        "occurred_at": datetime.now(UTC).isoformat(),
    }
    with _affiliate_lock:
        _analytics_events.append(event)
    return event


def get_affiliate_analytics_summary() -> dict[str, Any]:
    with _affiliate_lock:
        events = list(_analytics_events)
    totals = {"impression": 0, "click": 0, "conversion": 0}
    by_provider: dict[str, dict[str, int]] = {}
    for event in events:
        event_type = str(event.get("event_type"))
        provider = str(event.get("provider") or "unknown")
        if event_type in totals:
            totals[event_type] += 1
        provider_totals = by_provider.setdefault(provider, {"impression": 0, "click": 0, "conversion": 0})
        if event_type in provider_totals:
            provider_totals[event_type] += 1
    click_rate = (totals["click"] / totals["impression"]) if totals["impression"] else 0.0
    conversion_rate = (totals["conversion"] / totals["click"]) if totals["click"] else 0.0
    return {
        "totals": totals,
        "click_through_rate": round(click_rate, 4),
        "conversion_rate": round(conversion_rate, 4),
        "by_provider": by_provider,
        "event_count": len(events),
    }


_seed_defaults()
