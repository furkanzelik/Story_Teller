from datetime import UTC, datetime, timedelta

from app.models import Subscription, SubscriptionStatus, UsageEvent


def test_free_user_subscription_shows_quota(client, db_session, test_user):
    db_session.add(
        UsageEvent(
            user_id=test_user.id,
            kind="story_generated",
            created_at=datetime.now(UTC) - timedelta(hours=1),
        )
    )
    db_session.flush()

    r = client.get("/me/subscription")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "free"
    assert body["quota"] == {
        "unlimited": False,
        "limit": 2,
        "used": 1,
        "remaining": 1,
        "resets_at": body["quota"]["resets_at"],
    }


def test_subscriber_subscription_is_unlimited(client, db_session, test_user):
    db_session.add(
        Subscription(
            user_id=test_user.id,
            status=SubscriptionStatus.active,
            plan="plus_monthly",
            provider="revenuecat",
        )
    )
    db_session.flush()

    r = client.get("/me/subscription")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "active"
    assert body["plan"] == "plus_monthly"
    assert body["quota"]["unlimited"] is True
    assert body["quota"]["remaining"] == -1


def test_subscription_requires_auth(monkeypatch):
    from dataclasses import dataclass

    from fastapi.testclient import TestClient

    from app.main import app

    @dataclass
    class _S:
        supabase_jwt_secret: str | None = "s"
        supabase_url: str | None = None
        supabase_jwt_audience: str = "authenticated"

    monkeypatch.setattr("app.core.security.get_settings", lambda: _S())
    assert TestClient(app).get("/me/subscription").status_code == 401
