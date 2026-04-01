from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from app.core.auth import AuthUser, get_current_user
from app.core.notifications import (
    get_notification_preferences,
    list_notifications,
    mark_notification_read,
    save_notification_preferences,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/preferences", status_code=status.HTTP_200_OK)
def get_preferences(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    return get_notification_preferences(user.email)


@router.put("/preferences", status_code=status.HTTP_200_OK)
def update_preferences(
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    return save_notification_preferences(user.email, payload)


@router.get("", status_code=status.HTTP_200_OK)
def get_notification_feed(
    unread_only: bool = Query(default=False),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    items = list_notifications(user.email, unread_only=unread_only)
    unread_count = len([item for item in items if not item.get("read")])
    return {
        "items": items,
        "total": len(items),
        "unread_count": unread_count,
    }


@router.patch("/{notification_id}", status_code=status.HTTP_200_OK)
def update_notification_state(
    notification_id: str,
    payload: dict[str, object] = Body(...),
    user: AuthUser = Depends(get_current_user),
) -> dict[str, object]:
    read = payload.get("read")
    if not isinstance(read, bool):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Field 'read' must be a boolean")
    updated = mark_notification_read(user.email, notification_id, read=read)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return updated
