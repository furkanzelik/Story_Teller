from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.core.config import get_settings
from app.models import Subscription, SubscriptionStatus, UsageEvent
from app.services.quota import (
    enforce_free_quota,
    get_quota_status,
    next_week_start,
    week_start,
)


def _generated(db, user_id, n, *, age=timedelta(hours=1)):
    for _ in range(n):
        db.add(
            UsageEvent(
                user_id=user_id,
                kind="story_generated",
                created_at=datetime.now(UTC) - age,
            )
        )
    db.flush()


@pytest.fixture
def settings():
    s = get_settings()
    assert s.free_stories_per_week == 2  # test assumes the default
    return s


def test_free_user_within_quota(db_session, test_user, settings):
    _generated(db_session, test_user.id, 1)
    q = get_quota_status(db_session, test_user, settings)
    assert not q.unlimited
    assert q.used == 1 and q.remaining == 1 and not q.exhausted
    enforce_free_quota(db_session, test_user, settings)  # no raise


def test_free_user_at_quota_raises_402(db_session, test_user, settings):
    _generated(db_session, test_user.id, 2)
    q = get_quota_status(db_session, test_user, settings)
    assert q.exhausted and q.remaining == 0
    with pytest.raises(HTTPException) as exc:
        enforce_free_quota(db_session, test_user, settings)
    assert exc.value.status_code == 402
    assert exc.value.detail["reason"] == "free_quota_exhausted"


def test_last_weeks_stories_do_not_count(db_session, test_user, settings):
    _generated(db_session, test_user.id, 5, age=timedelta(days=8))
    q = get_quota_status(db_session, test_user, settings)
    assert q.used == 0
    enforce_free_quota(db_session, test_user, settings)  # no raise


def test_subscriber_is_unlimited(db_session, test_user, settings):
    db_session.add(
        Subscription(
            user_id=test_user.id,
            status=SubscriptionStatus.active,
            provider="revenuecat",
        )
    )
    _generated(db_session, test_user.id, 50)
    q = get_quota_status(db_session, test_user, settings)
    assert q.unlimited and q.remaining == -1
    enforce_free_quota(db_session, test_user, settings)  # no raise


def test_grace_period_is_unlimited(db_session, test_user, settings):
    db_session.add(
        Subscription(
            user_id=test_user.id,
            status=SubscriptionStatus.in_grace,
            provider="revenuecat",
        )
    )
    _generated(db_session, test_user.id, 10)
    assert get_quota_status(db_session, test_user, settings).unlimited


def test_expired_subscriber_falls_back_to_free_limit(db_session, test_user, settings):
    db_session.add(
        Subscription(
            user_id=test_user.id,
            status=SubscriptionStatus.expired,
            provider="revenuecat",
        )
    )
    _generated(db_session, test_user.id, 2)
    with pytest.raises(HTTPException):
        enforce_free_quota(db_session, test_user, settings)


def test_week_boundaries_are_monday_utc():
    ws = week_start()
    assert ws.weekday() == 0 and ws.hour == 0 and ws.tzinfo == UTC
    assert next_week_start() - ws == timedelta(days=7)
