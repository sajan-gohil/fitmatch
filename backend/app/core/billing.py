from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Literal

from fastapi import HTTPException, status

from app.core.phase11_extensions import apply_referral_credit_for_paid_plan
from app.core.settings import get_settings

PlanName = Literal["free", "pro", "lifetime"]


@dataclass(frozen=True)
class SubscriptionState:
    plan: PlanName
    status: str
    razorpay_customer_id: str | None = None
    razorpay_subscription_id: str | None = None
    razorpay_order_id: str | None = None
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
        return f"order_test_{_session_counter:06d}"


def create_checkout_session(user_email: str, plan: PlanName) -> dict[str, str]:
    settings = get_settings()
    plan_id = settings.razorpay_pro_plan_id if plan == "pro" else settings.razorpay_lifetime_plan_id
    session_id = _next_checkout_session_id()
    session = {
        "id": session_id,
        "url": f"https://rzp.io/i/{session_id}",
        "plan_id": plan_id,
        "plan": plan,
        "customer_email": user_email,
    }
    _checkout_sessions[session_id] = session
    return session


def create_billing_portal_session(user_email: str) -> dict[str, str]:
    customer_id = get_subscription_state(user_email).razorpay_customer_id or f"cust_{hashlib.sha256(user_email.encode()).hexdigest()[:10]}"
    return {
        "url": f"https://dashboard.razorpay.com/app/subscriptions/{customer_id}",
    }


def _normalize_plan(value: str | None) -> PlanName:
    if not value:
        return "free"
    normalized = value.strip().lower()
    settings = get_settings()
    if normalized in {"lifetime", settings.razorpay_lifetime_plan_id.lower()}:
        return "lifetime"
    if normalized in {"pro", settings.razorpay_pro_plan_id.lower()}:
        return "pro"
    return "free"


def verify_webhook_signature(payload: bytes, signature: str | None) -> None:
    secret = get_settings().razorpay_webhook_secret
    if not secret:
        return
    if not signature:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing webhook signature")
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")


def _coerce_entity(payload: object, key: str) -> dict[str, object]:
    if not isinstance(payload, dict):
        return {}
    container = payload.get(key)
    if not isinstance(container, dict):
        return {}
    entity = container.get("entity")
    if not isinstance(entity, dict):
        return {}
    return entity


def _extract_email(subscription: dict[str, object], payment: dict[str, object], customer: dict[str, object]) -> str:
    notes = subscription.get("notes")
    if isinstance(notes, dict):
        email = notes.get("email") or notes.get("customer_email")
        if isinstance(email, str) and email.strip():
            return email.strip().lower()
    for candidate in (payment.get("email"), customer.get("email"), subscription.get("customer_email")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip().lower()
    return ""


def apply_webhook_event(payload: bytes) -> dict[str, object]:
    event = json.loads(payload.decode("utf-8"))
    event_type = str(event.get("event", ""))
    event_payload = event.get("payload", {}) if isinstance(event, dict) else {}
    subscription = _coerce_entity(event_payload, "subscription")
    payment = _coerce_entity(event_payload, "payment")
    customer = _coerce_entity(event_payload, "customer")
    email = _extract_email(subscription, payment, customer)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook event missing customer email")

    current = get_subscription_state(email)
    updated = current

    if event_type in {"subscription.activated", "subscription.charged", "subscription.completed", "payment.captured"}:
        plan_source = subscription.get("plan_id")
        if not isinstance(plan_source, str):
            notes = subscription.get("notes")
            if isinstance(notes, dict):
                plan_source = notes.get("plan")
        plan = _normalize_plan(plan_source if isinstance(plan_source, str) else None)
        period_end_raw = subscription.get("current_end")
        period_end = None
        if isinstance(period_end_raw, (int, float)):
            period_end = datetime.fromtimestamp(period_end_raw, tz=timezone.utc)
        customer_id = subscription.get("customer_id") if isinstance(subscription.get("customer_id"), str) else None
        if not customer_id and isinstance(customer.get("id"), str):
            customer_id = customer["id"]
        subscription_id = subscription.get("id") if isinstance(subscription.get("id"), str) else None
        order_id = payment.get("order_id") if isinstance(payment.get("order_id"), str) else None
        updated = SubscriptionState(
            plan=plan,
            status=str(subscription.get("status") or payment.get("status") or "active"),
            razorpay_customer_id=customer_id,
            razorpay_subscription_id=subscription_id,
            razorpay_order_id=order_id,
            period_end=period_end,
            checkout_session_id=order_id,
        )
    elif event_type in {"subscription.cancelled"}:
        updated = SubscriptionState(
            plan="free",
            status="canceled",
            razorpay_customer_id=current.razorpay_customer_id,
        )

    _subscriptions[email] = updated
    if event_type in {"subscription.activated", "subscription.charged", "subscription.completed", "payment.captured"} and updated.plan in {"pro", "lifetime"}:
        apply_referral_credit_for_paid_plan(email)
    return {
        "received": True,
        "event_type": event_type,
        "plan": updated.plan,
        "status": updated.status,
    }
