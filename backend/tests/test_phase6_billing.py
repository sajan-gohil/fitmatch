from __future__ import annotations

import hashlib
import hmac
import json

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.settings import get_settings
from app.main import app

client = TestClient(app)


def _auth_headers(email: str = "phase6@example.com") -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "provider": "magic_link"})
    assert login.status_code == 202
    token = login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_checkout_session_supports_pro_and_lifetime() -> None:
    headers = _auth_headers("phase6-checkout@example.com")

    pro = client.post("/api/billing/checkout-session", headers=headers, json={"plan": "pro"})
    assert pro.status_code == 200
    assert pro.json()["plan_id"] == "plan_pro_monthly"

    lifetime = client.post("/api/billing/checkout-session", headers=headers, json={"plan": "lifetime"})
    assert lifetime.status_code == 200
    assert lifetime.json()["plan_id"] == "plan_lifetime_one_time"


def test_billing_portal_session_available() -> None:
    headers = _auth_headers("phase6-portal@example.com")
    response = client.post("/api/billing/portal-session", headers=headers)
    assert response.status_code == 200
    assert response.json()["url"].startswith("https://dashboard.razorpay.com/app/subscriptions/")


def test_webhook_updates_entitlements_with_signature(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("FITMATCH_RAZORPAY_WEBHOOK_SECRET", "whsec_phase6")
    get_settings.cache_clear()
    email = "phase6-entitlements@example.com"
    headers = _auth_headers(email)
    payload = {
        "event": "subscription.activated",
        "payload": {
            "subscription": {
                "entity": {
                    "id": "sub_phase6",
                    "customer_id": "cust_phase6",
                    "status": "active",
                    "plan_id": "plan_lifetime_one_time",
                    "current_end": 1767225600,
                    "notes": {"email": email},
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_phase6",
                    "order_id": "order_phase6",
                    "status": "captured",
                }
            },
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = hmac.new(b"whsec_phase6", payload_bytes, hashlib.sha256).hexdigest()

    webhook = client.post(
        "/api/billing/webhook",
        content=payload_bytes,
        headers={"X-Razorpay-Signature": signature},
    )
    assert webhook.status_code == 200
    assert webhook.json()["plan"] == "lifetime"

    entitlements = client.get("/api/billing/entitlements", headers=headers)
    assert entitlements.status_code == 200
    assert entitlements.json()["plan"] == "lifetime"
    assert entitlements.json()["is_paid"] is True
    get_settings.cache_clear()
