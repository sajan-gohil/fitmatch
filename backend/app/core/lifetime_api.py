from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.core.auth import AuthUser, get_current_user
from app.core.tiers import get_user_tier
from app.core.settings import get_settings


@dataclass(frozen=True)
class LifetimeApiToken:
    token_id: str
    owner_email: str
    token_hash: str
    label: str
    created_at: str
    revoked_at: str | None = None


_token_lock = Lock()
_tokens_by_owner: dict[str, list[LifetimeApiToken]] = {}
_token_hash_index: dict[str, LifetimeApiToken] = {}
_quota_usage: dict[str, int] = {}
_api_key_header = APIKeyHeader(name="X-FitMatch-API-Key", auto_error=False)


def reset_lifetime_api_state() -> None:
    with _token_lock:
        _tokens_by_owner.clear()
        _token_hash_index.clear()
        _quota_usage.clear()


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _today_key(owner_email: str, token_id: str) -> str:
    day = datetime.now(UTC).date().isoformat()
    return f"{owner_email}|{token_id}|{day}"


def issue_lifetime_api_token(owner_email: str, label: str) -> dict[str, str]:
    if get_user_tier(owner_email) != "lifetime":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lifetime plan required for API access.",
        )
    cleaned_label = label.strip() or "default"
    raw_token = f"fm_api_{secrets.token_urlsafe(32)}"
    token_hash = _hash_token(raw_token)
    token = LifetimeApiToken(
        token_id=f"tok_{secrets.token_hex(8)}",
        owner_email=owner_email,
        token_hash=token_hash,
        label=cleaned_label,
        created_at=datetime.now(UTC).isoformat(),
    )
    with _token_lock:
        _tokens_by_owner.setdefault(owner_email, []).append(token)
        _token_hash_index[token_hash] = token
    return {
        "token": raw_token,
        "token_id": token.token_id,
        "label": token.label,
        "created_at": token.created_at,
    }


def list_lifetime_api_tokens(owner_email: str) -> list[dict[str, Any]]:
    with _token_lock:
        tokens = list(_tokens_by_owner.get(owner_email, []))
    return [
        {
            "token_id": item.token_id,
            "label": item.label,
            "created_at": item.created_at,
            "revoked_at": item.revoked_at,
        }
        for item in sorted(tokens, key=lambda row: row.created_at, reverse=True)
    ]


def revoke_lifetime_api_token(owner_email: str, token_id: str) -> bool:
    with _token_lock:
        rows = _tokens_by_owner.get(owner_email, [])
        updated_rows: list[LifetimeApiToken] = []
        revoked = False
        for item in rows:
            if item.token_id == token_id and item.revoked_at is None:
                revoked_item = LifetimeApiToken(
                    token_id=item.token_id,
                    owner_email=item.owner_email,
                    token_hash=item.token_hash,
                    label=item.label,
                    created_at=item.created_at,
                    revoked_at=datetime.now(UTC).isoformat(),
                )
                updated_rows.append(revoked_item)
                _token_hash_index[item.token_hash] = revoked_item
                revoked = True
            else:
                updated_rows.append(item)
        _tokens_by_owner[owner_email] = updated_rows
        return revoked


def _resolve_token(raw_token: str) -> LifetimeApiToken | None:
    token_hash = _hash_token(raw_token)
    with _token_lock:
        token = _token_hash_index.get(token_hash)
    if token is None or token.revoked_at is not None:
        return None
    return token


def enforce_lifetime_api_quota(token: LifetimeApiToken) -> dict[str, int]:
    daily_quota = max(1, get_settings().lifetime_api_daily_quota)
    key = _today_key(token.owner_email, token.token_id)
    with _token_lock:
        used = _quota_usage.get(key, 0)
        if used >= daily_quota:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Lifetime API daily quota exceeded.",
            )
        used += 1
        _quota_usage[key] = used
    return {"quota_daily": daily_quota, "quota_used": used, "quota_remaining": max(0, daily_quota - used)}


def get_lifetime_api_caller(
    api_key: str | None = Depends(_api_key_header),
) -> dict[str, Any]:
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    token = _resolve_token(api_key.strip())
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    if get_user_tier(token.owner_email) != "lifetime":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lifetime plan required for API access.")
    quota = enforce_lifetime_api_quota(token)
    return {"owner_email": token.owner_email, "token_id": token.token_id, **quota}


def ensure_lifetime_plan(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    if get_user_tier(user.email) != "lifetime":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Lifetime plan required for API access.")
    return user
