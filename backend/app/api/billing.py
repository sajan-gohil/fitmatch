from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel

from app.core.auth import AuthUser, get_current_user
from app.core.billing import (
    apply_webhook_event,
    create_billing_portal_session,
    create_checkout_session,
    get_subscription_state,
    verify_webhook_signature,
)

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan: Literal["pro", "lifetime"]


@router.get("/entitlements", status_code=status.HTTP_200_OK)
def get_entitlements(user: AuthUser = Depends(get_current_user)) -> dict[str, object]:
    subscription = get_subscription_state(user.email)
    return {
        "plan": subscription.plan,
        "status": subscription.status,
        "is_paid": subscription.plan in {"pro", "lifetime"},
    }


@router.post("/checkout-session", status_code=status.HTTP_200_OK)
def create_checkout(payload: CheckoutRequest, user: AuthUser = Depends(get_current_user)) -> dict[str, str]:
    return create_checkout_session(user.email, payload.plan)


@router.post("/portal-session", status_code=status.HTTP_200_OK)
def create_portal(user: AuthUser = Depends(get_current_user)) -> dict[str, str]:
    return create_billing_portal_session(user.email)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> dict[str, object]:
    payload = await request.body()
    verify_webhook_signature(payload, stripe_signature)
    return apply_webhook_event(payload)
