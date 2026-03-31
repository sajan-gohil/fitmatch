from __future__ import annotations

import secrets
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


@dataclass(frozen=True)
class AuthUser:
    email: str


_token_store: dict[str, AuthUser] = {}
_http_bearer = HTTPBearer(auto_error=False)


def issue_session_token(email: str) -> str:
    token = secrets.token_urlsafe(32)
    _token_store[token] = AuthUser(email=email.strip().lower())
    return token


def get_user_from_token(token: str) -> AuthUser | None:
    return _token_store.get(token)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_http_bearer),
) -> AuthUser:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    user = get_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    return user
