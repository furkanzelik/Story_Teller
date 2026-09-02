from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.models import UsageEvent
from app.services.rate_limit import enforce_rate_limit


def _seed(db, user_id, kind, n, *, age=timedelta(minutes=1)):
    for _ in range(n):
        db.add(
            UsageEvent(
                user_id=user_id,
                kind=kind,
                created_at=datetime.now(UTC) - age,
            )
        )
    db.flush()


def test_under_limit_passes(db_session, test_user):
    _seed(db_session, test_user.id, "generation_attempt", 3)
    enforce_rate_limit(
        db_session, test_user.id, kind="generation_attempt", limit=5
    )  # no raise


def test_at_limit_raises_429(db_session, test_user):
    _seed(db_session, test_user.id, "generation_attempt", 5)
    with pytest.raises(HTTPException) as exc:
        enforce_rate_limit(
            db_session, test_user.id, kind="generation_attempt", limit=5
        )
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_old_events_fall_out_of_window(db_session, test_user):
    _seed(
        db_session,
        test_user.id,
        "generation_attempt",
        10,
        age=timedelta(hours=2),  # outside the 1h window
    )
    enforce_rate_limit(
        db_session, test_user.id, kind="generation_attempt", limit=5
    )  # no raise


def test_other_users_events_do_not_count(db_session, test_user, other_user):
    _seed(db_session, other_user.id, "generation_attempt", 20)
    enforce_rate_limit(
        db_session, test_user.id, kind="generation_attempt", limit=5
    )  # no raise


@pytest.fixture
def other_user(db_session):
    from app.models import User

    u = User(email="rl-other@example.com", auth_provider="supabase", auth_subject="rl-other")
    db_session.add(u)
    db_session.flush()
    return u
