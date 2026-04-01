from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.core.affiliate import (
    build_contextual_course_placements,
    get_affiliate_analytics_summary,
    list_provider_adapters,
    list_skill_course_mappings,
    recommend_courses_for_skills,
    suggest_ai_skill_course_mappings,
    sync_catalog,
    track_affiliate_event,
    upsert_skill_course_mapping,
)
from app.core.auth import AuthUser, get_current_user

router = APIRouter(prefix="/affiliate", tags=["affiliate"])


@router.get("/providers", status_code=status.HTTP_200_OK)
def get_providers(_: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return {"providers": list_provider_adapters()}


@router.post("/catalog/sync", status_code=status.HTTP_200_OK)
def sync_catalog_endpoint(
    payload: dict[str, object] = Body(default={}),
    _: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    skills_raw = payload.get("skills", [])
    skills = [str(item) for item in skills_raw] if isinstance(skills_raw, list) else []
    force = bool(payload.get("force", False))
    return sync_catalog(skills=skills, force=force)


@router.get("/recommendations", status_code=status.HTTP_200_OK)
def get_recommendations(
    skills: str = Query(default="", description="Comma-separated skills"),
    per_skill_limit: int = Query(default=2, ge=1, le=3),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    skill_list = [item.strip() for item in skills.split(",") if item.strip()]
    recommendations = recommend_courses_for_skills(skill_list, per_skill_limit=per_skill_limit)
    for entry in recommendations:
        skill = entry.get("skill")
        courses = entry.get("courses", [])
        if not isinstance(courses, list):
            continue
        for course in courses:
            if not isinstance(course, dict):
                continue
            provider = str(course.get("provider") or "")
            external_course_id = str(course.get("external_course_id") or "")
            if provider and external_course_id:
                track_affiliate_event(
                    user_email=user.email,
                    event_type="impression",
                    provider=provider,
                    external_course_id=external_course_id,
                    skill=str(skill) if isinstance(skill, str) else None,
                    metadata={"source": "recommendations_api"},
                )
    return {"recommendations": recommendations, "total_skills": len(recommendations)}


@router.post("/placements", status_code=status.HTTP_200_OK)
def get_contextual_placements(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    missing_skills_raw = payload.get("missing_skills", [])
    resume_scoring_payload = payload.get("resume_scoring", {})
    missing_skills = [str(item) for item in missing_skills_raw] if isinstance(missing_skills_raw, list) else []
    resume_scoring = resume_scoring_payload if isinstance(resume_scoring_payload, dict) else {}
    placements = build_contextual_course_placements(
        missing_skills=missing_skills,
        resume_scoring=resume_scoring,
    )
    for slot in placements.get("gap_report_courses", []):
        if not isinstance(slot, dict):
            continue
        skill = str(slot.get("skill") or "")
        courses = slot.get("courses", [])
        if not isinstance(courses, list):
            continue
        for course in courses:
            if not isinstance(course, dict):
                continue
            provider = str(course.get("provider") or "")
            external_course_id = str(course.get("external_course_id") or "")
            if provider and external_course_id:
                track_affiliate_event(
                    user_email=user.email,
                    event_type="impression",
                    provider=provider,
                    external_course_id=external_course_id,
                    skill=skill,
                    metadata={"source": "contextual_placements"},
                )
    return placements


@router.post("/events", status_code=status.HTTP_201_CREATED)
def create_affiliate_event(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    event_type = str(payload.get("event_type") or "").strip().lower()
    provider = str(payload.get("provider") or "").strip().lower()
    external_course_id = str(payload.get("external_course_id") or "").strip()
    if event_type not in {"impression", "click", "conversion"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid event_type")
    if not provider or not external_course_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="provider and external_course_id are required")
    event = track_affiliate_event(
        user_email=user.email,
        event_type=event_type,  # type: ignore[arg-type]
        provider=provider,
        external_course_id=external_course_id,
        skill=str(payload.get("skill")) if payload.get("skill") is not None else None,
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
    )
    return event


@router.get("/analytics", status_code=status.HTTP_200_OK)
def get_analytics(_: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return get_affiliate_analytics_summary()


@router.get("/admin/mappings", status_code=status.HTTP_200_OK)
def get_skill_mappings(_: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_skill_course_mappings()}


@router.put("/admin/mappings", status_code=status.HTTP_200_OK)
def put_skill_mapping(
    payload: dict[str, object] = Body(...),
    _: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    try:
        mapping = upsert_skill_course_mapping(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return mapping


@router.post("/admin/mappings/suggest", status_code=status.HTTP_200_OK)
def suggest_skill_mappings(
    payload: dict[str, object] = Body(...),
    _: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    skills_raw = payload.get("skills", [])
    skills = [str(item) for item in skills_raw] if isinstance(skills_raw, list) else []
    return {"suggestions": suggest_ai_skill_course_mappings(skills)}
