from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from fastapi import HTTPException, status

from app.core.settings import get_settings

PlanName = Literal["free", "pro", "lifetime"]


@dataclass(frozen=True)
class SubscriptionState:
    plan: PlanName
    status: str
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    period_end: datetime | None = None
    checkout_session_id: str | None = None


_subscriptions: dict[str, SubscriptionState] = {}
_checkout_sessions: dict[str, dict[str, str]] = {}
_session_counter = 0
_session_counter_lock = Lock()
# NOTE: Billing state is intentionally in-memory for scaffold phases and tests.
# Production should persist subscriptions/sessions in the database.
# NOTE: Generated checkout/customer values are mock identifiers for scaffold-only flows.


def get_subscription_state(user_email: str) -> SubscriptionState:
    return _subscriptions.get(user_email, SubscriptionState(plan="free", status="active"))


def get_plan_for_user(user_email: str) -> PlanName:
    return get_subscription_state(user_email).plan


def _next_checkout_session_id() -> str:
    global _session_counter
    with _session_counter_lock:
        _session_counter += 1
        return f"cs_test_{_session_counter:06d}"


def create_checkout_session(user_email: str, plan: PlanName) -> dict[str, str]:
    settings = get_settings()
    price_id = settings.stripe_pro_price_id if plan == "pro" else settings.stripe_lifetime_price_id
    session_id = _next_checkout_session_id()
    session = {
        "id": session_id,
        "url": f"https://checkout.stripe.com/pay/{session_id}",
        "price_id": price_id,
        "plan": plan,
        "customer_email": user_email,
    }
    _checkout_sessions[session_id] = session
    return session


def create_billing_portal_session(user_email: str) -> dict[str, str]:
    # Fallback customer ID supports local scaffold/demo usage when no Stripe customer exists yet.
    customer_id = get_subscription_state(user_email).stripe_customer_id or f"cus_{hashlib.sha256(user_email.encode()).hexdigest()[:10]}"
    return {
        "url": f"https://billing.stripe.com/p/session/{customer_id}",
    }


def _normalize_plan(value: str | None) -> PlanName:
    if value == "lifetime":
        return "lifetime"
    if value == "pro":
        return "pro"
    return "free"


def verify_webhook_signature(payload: bytes, signature: str | None) -> None:
    secret = get_settings().stripe_webhook_secret
    if not secret:
        return
    if not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook signature")
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")


def apply_webhook_event(payload: bytes) -> dict[str, object]:
    event = json.loads(payload.decode("utf-8"))
    event_type = str(event.get("type", ""))
    data = event.get("data", {})
    data_object = data.get("object", {}) if isinstance(data, dict) else {}
    email = str(data_object.get("customer_email", "")).strip().lower()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook event missing customer_email")

    current = get_subscription_state(email)
    updated = current

    if event_type in {"checkout.session.completed", "customer.subscription.updated"}:
        plan = _normalize_plan(str(data_object.get("plan", "")))
        period_end_raw = data_object.get("period_end")
        period_end = None
        if isinstance(period_end_raw, (int, float)):
            period_end = datetime.fromtimestamp(period_end_raw, tz=timezone.utc)
        updated = SubscriptionState(
            plan=plan,
            status=str(data_object.get("status", "active")),
            stripe_customer_id=data_object.get("customer"),
            stripe_subscription_id=data_object.get("subscription"),
            period_end=period_end,
            checkout_session_id=data_object.get("id"),
        )
    elif event_type in {"customer.subscription.deleted"}:
        updated = SubscriptionState(plan="free", status="canceled", stripe_customer_id=current.stripe_customer_id)

    _subscriptions[email] = updated
    return {
        "received": True,
        "event_type": event_type,
        "plan": updated.plan,
        "status": updated.status,
    }
