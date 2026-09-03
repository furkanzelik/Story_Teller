"""Free-tier story quota (Fase 5 stap 16).

A non-subscriber gets `free_stories_per_week` successful generations per
calendar week (Monday 00:00 UTC). Subscribers (`active` / `in_grace`) are
unlimited. Counted on `story_generated` events so a failed run never costs the
user a story.

Separate from `services/rate_limit.py`: that one is an anti-abuse throttle on
*attempts*; this one is the business limit on *successes*.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import Subscription, SubscriptionStatus, UsageEvent, User

_UNLIMITED_STATUSES = {SubscriptionStatus.active, SubscriptionStatus.in_grace}


def week_start(now: datetime | None = None) -> datetime:
    now = now or datetime.now(UTC)
    monday = now - timedelta(days=now.weekday())
    return monday.replace(hour=0, minute=0, second=0, microsecond=0)


def next_week_start(now: datetime | None = None) -> datetime:
    return week_start(now) + timedelta(days=7)


@dataclass(frozen=True)
class QuotaStatus:
    unlimited: bool
    limit: int
    used: int
    resets_at: datetime

    @property
    def remaining(self) -> int:
        return -1 if self.unlimited else max(0, self.limit - self.used)

    @property
    def exhausted(self) -> bool:
        return not self.unlimited and self.used >= self.limit


def _subscription_status(db: Session, user: User) -> SubscriptionStatus:
    sub = db.scalar(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    return sub.status if sub else SubscriptionStatus.free


def get_quota_status(db: Session, user: User, settings: Settings) -> QuotaStatus:
    status_ = _subscription_status(db, user)
    if status_ in _UNLIMITED_STATUSES:
        return QuotaStatus(
            unlimited=True,
            limit=settings.free_stories_per_week,
            used=0,
            resets_at=next_week_start(),
        )

    used = db.scalar(
        select(func.count())
        .select_from(UsageEvent)
        .where(
            UsageEvent.user_id == user.id,
            UsageEvent.kind == "story_generated",
            UsageEvent.created_at >= week_start(),
        )
    ) or 0
    return QuotaStatus(
        unlimited=False,
        limit=settings.free_stories_per_week,
        used=used,
        resets_at=next_week_start(),
    )


def enforce_free_quota(db: Session, user: User, settings: Settings) -> None:
    quota = get_quota_status(db, user, settings)
    if quota.exhausted:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "reason": "free_quota_exhausted",
                "message": "Je gratis verhaaltjes voor deze week zijn op.",
                "limit": quota.limit,
                "used": quota.used,
                "resets_at": quota.resets_at.isoformat(),
            },
        )
