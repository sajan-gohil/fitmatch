from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.core.auth import AuthUser, get_current_user
from app.core.phase10_growth import (
    add_watchlist_company,
    delete_application_entry,
    get_scraper_scaling_controls,
    list_application_entries,
    list_watchlist_companies,
    queue_partition_for_source,
    remove_watchlist_company,
    salary_benchmark_by_role_location,
    upsert_application_entry,
)

router = APIRouter(prefix="/growth", tags=["growth"])


@router.get("/watchlist", status_code=status.HTTP_200_OK)
def get_watchlist(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    items = list_watchlist_companies(user.email)
    return {"items": items, "total": len(items)}


@router.post("/watchlist", status_code=status.HTTP_201_CREATED)
def create_watchlist_item(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    company_name = str(payload.get("company_name") or "").strip()
    if not company_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="company_name is required")
    try:
        item = add_watchlist_company(user.email, company_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return item


@router.delete("/watchlist/{watchlist_id}", status_code=status.HTTP_200_OK)
def delete_watchlist_item(watchlist_id: str, user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    deleted = remove_watchlist_company(user.email, watchlist_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist item not found")
    return {"deleted": True}


@router.get("/applications", status_code=status.HTTP_200_OK)
def get_application_tracker(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    items = list_application_entries(user.email)
    return {"items": items, "total": len(items)}


@router.put("/applications", status_code=status.HTTP_200_OK)
def put_application_entry(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    external_job_id = str(payload.get("external_job_id") or "").strip()
    status_raw = str(payload.get("status") or "").strip()
    if not external_job_id or not status_raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="external_job_id and status are required",
        )
    try:
        row = upsert_application_entry(
            user.email,
            external_job_id=external_job_id,
            status=status_raw,
            notes=str(payload.get("notes") or ""),
            applied_at=(str(payload.get("applied_at")) if payload.get("applied_at") is not None else None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return row


@router.delete("/applications/{application_id}", status_code=status.HTTP_200_OK)
def delete_application(application_id: str, user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    deleted = delete_application_entry(user.email, application_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application entry not found")
    return {"deleted": True}


@router.get("/salary-benchmark", status_code=status.HTTP_200_OK)
def get_salary_benchmark(
    role: str | None = Query(default=None),
    location: str | None = Query(default=None),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    del user
    benchmark = salary_benchmark_by_role_location(role=role, location=location)
    return {
        "role_filter": role,
        "location_filter": location,
        **benchmark,
    }


@router.get("/scraper-controls", status_code=status.HTTP_200_OK)
def get_scaling_controls(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    del user
    controls = get_scraper_scaling_controls()
    return {"controls": controls}


@router.get("/scraper-controls/partition", status_code=status.HTTP_200_OK)
def get_partition_for_source(
    source_url: str = Query(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    del user
    if not source_url.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="source_url is required")
    return {
        "source_url": source_url,
        "partition": queue_partition_for_source(source_url.strip()),
        "queue_partitions": get_scraper_scaling_controls()["queue_partitions"],
    }
