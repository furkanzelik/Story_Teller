"""RevenueCat webhook (Fase 5 stap 15).

Fully wired; it just needs `REVENUECAT_WEBHOOK_AUTH` set to the value you put in
RevenueCat -> Project settings -> Webhooks -> "Authorization header". RevenueCat
sends that string verbatim as the `Authorization` header on every call.

The app must initialise the RevenueCat SDK with `appUserID = <our users.id>` so
`event.app_user_id` maps straight to a local user.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models import Subscription, SubscriptionStatus, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# RevenueCat event type -> our subscription status.
_EVENT_STATUS: dict[str, SubscriptionStatus] = {
    "INITIAL_PURCHASE": SubscriptionStatus.active,
    "RENEWAL": SubscriptionStatus.active,
    "UNCANCELLATION": SubscriptionStatus.active,
    "PRODUCT_CHANGE": SubscriptionStatus.active,
    "NON_RENEWING_PURCHASE": SubscriptionStatus.active,
    "CANCELLATION": SubscriptionStatus.active,  # access lasts until expiration
    "BILLING_ISSUE": SubscriptionStatus.in_grace,
    "SUBSCRIPTION_PAUSED": SubscriptionStatus.expired,
    "EXPIRATION": SubscriptionStatus.expired,
}


@router.post("/revenuecat", status_code=status.HTTP_200_OK)
async def revenuecat_webhook(
    request: Request,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()
    expected = settings.revenuecat_webhook_auth
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RevenueCat webhook is not configured.",
        )
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    body = await request.json()
    event = body.get("event", {})
    event_type = event.get("type", "")
    app_user_id = event.get("app_user_id")

    new_status = _EVENT_STATUS.get(event_type)
    if new_status is None:
        logger.info("revenuecat: ignoring event type %s", event_type)
        return {"ok": True, "ignored": event_type}

    user = _lookup_user(db, app_user_id)
    if user is None:
        logger.warning("revenuecat: no user for app_user_id %s", app_user_id)
        return {"ok": True, "unmatched": True}

    sub = db.scalar(select(Subscription).where(Subscription.user_id == user.id))
    if sub is None:
        sub = Subscription(user_id=user.id, provider="revenuecat")
        db.add(sub)

    sub.status = new_status
    sub.provider = "revenuecat"
    sub.plan = event.get("product_id") or sub.plan
    if cust := (event.get("original_app_user_id") or app_user_id):
        sub.provider_customer_id = str(cust)
    if exp_ms := event.get("expiration_at_ms"):
        sub.current_period_end = datetime.fromtimestamp(exp_ms / 1000, tz=UTC)

    db.commit()
    logger.info(
        "revenuecat: user %s -> %s (%s)", user.id, new_status.value, event_type
    )
    return {"ok": True}


def _lookup_user(db: Session, app_user_id) -> User | None:
    if not app_user_id:
        return None
    try:
        return db.get(User, app_user_id)  # app_user_id == our users.id (uuid)
    except Exception:  # malformed id
        return None
