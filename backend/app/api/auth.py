from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.auth import get_user_from_token, issue_session_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    provider: str = "magic_link"


class CallbackRequest(BaseModel):
    token: str


@router.post("/login", status_code=status.HTTP_202_ACCEPTED)
def login(payload: LoginRequest) -> dict[str, str]:
    email = payload.email.strip().lower()
    if "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email")

    provider = payload.provider.lower()
    if provider not in {"magic_link", "google"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="provider must be one of: magic_link, google",
        )

    token = issue_session_token(email)
    return {
        "status": "sent",
        "provider": provider,
        "token": token,
        "message": "Mock auth accepted for scaffold; exchange this token in /api/auth/callback.",
    }


@router.post("/callback")
def callback(payload: CallbackRequest) -> dict[str, object]:
    user = get_user_from_token(payload.token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return {"status": "authenticated", "token": payload.token, "user": {"email": user.email}}
