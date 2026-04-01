from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.core.auth import AuthUser, get_current_user
from app.core.phase11_extensions import (
    get_feature_flag_state,
    get_or_create_referral_code,
    get_queue_throughput_controls,
    get_referral_summary,
    get_salary_benchmark_cached,
    get_slack_preference,
    list_feature_flags,
    list_slack_events,
    queue_slack_alert,
    save_slack_preference,
    set_feature_flag_override,
    track_referral_signup,
    track_referral_signup_by_code,
    update_feature_flag,
)

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/feature-flags", status_code=status.HTTP_200_OK)
def get_user_feature_flags(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return {"flags": get_feature_flag_state(user.email)}


@router.get("/feature-flags/admin", status_code=status.HTTP_200_OK)
def get_admin_feature_flags(_: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return {"items": list_feature_flags()}


@router.put("/feature-flags/admin", status_code=status.HTTP_200_OK)
def put_admin_feature_flag(
    payload: dict[str, object] = Body(...),
    _: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    try:
        return update_feature_flag(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/feature-flags/overrides", status_code=status.HTTP_200_OK)
def put_feature_flag_override(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    try:
        return set_feature_flag_override(user.email, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/slack/preferences", status_code=status.HTTP_200_OK)
def get_slack_preferences(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return get_slack_preference(user.email)


@router.put("/slack/preferences", status_code=status.HTTP_200_OK)
def put_slack_preferences(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    return save_slack_preference(user.email, payload)


@router.post("/slack/alerts/test", status_code=status.HTTP_202_ACCEPTED)
def post_test_slack_alert(
    payload: dict[str, object] = Body(default={}),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    score_raw = payload.get("score")
    score = float(score_raw) if isinstance(score_raw, (int, float)) else None
    result = queue_slack_alert(
        user.email,
        title=str(payload.get("title") or "FitMatch Slack alert"),
        body=str(payload.get("body") or "You have a new high-fit opportunity."),
        score=score,
        metadata={"source": "test_endpoint"},
    )
    return result


@router.get("/slack/events", status_code=status.HTTP_200_OK)
def get_slack_event_feed(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    items = list_slack_events(user.email)
    return {"items": items, "total": len(items)}


@router.get("/referrals/code", status_code=status.HTTP_200_OK)
def get_referral_code(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return get_or_create_referral_code(user.email)


@router.post("/referrals/track", status_code=status.HTTP_201_CREATED)
def post_referral_tracking(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    referred_email = str(payload.get("referred_email") or "").strip().lower()
    referral_code = str(payload.get("referral_code") or "").strip()
    if not referred_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="referred_email is required")
    try:
        if referral_code:
            return track_referral_signup_by_code(referral_code=referral_code, referred_email=referred_email)
        return track_referral_signup(referrer_email=user.email, referred_email=referred_email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/referrals/summary", status_code=status.HTTP_200_OK)
def get_referral_dashboard(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return get_referral_summary(user.email)


@router.get("/performance/salary-benchmark", status_code=status.HTTP_200_OK)
def get_cached_salary_benchmark(
    role: str | None = Query(default=None),
    location: str | None = Query(default=None),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    del user
    return {
        "role_filter": role,
        "location_filter": location,
        **get_salary_benchmark_cached(role=role, location=location),
    }


@router.get("/performance/queue-controls", status_code=status.HTTP_200_OK)
def get_perf_queue_controls(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    del user
    return {"controls": get_queue_throughput_controls()}

