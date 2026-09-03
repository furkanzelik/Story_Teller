from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import Subscription, SubscriptionStatus

_AUTH = "Bearer test-rc-secret"


@dataclass
class _S:
    revenuecat_webhook_auth: str | None = _AUTH


@pytest.fixture(autouse=True)
def _configured(monkeypatch):
    monkeypatch.setattr("app.api.routes.webhooks.get_settings", lambda: _S())


def _post(client, body, auth=_AUTH):
    headers = {"Authorization": auth} if auth else {}
    return client.post("/webhooks/revenuecat", json=body, headers=headers)


def _event(type_, user_id, **extra):
    return {"event": {"type": type_, "app_user_id": str(user_id), **extra}}


def test_missing_auth_rejected(client):
    r = _post(client, _event("INITIAL_PURCHASE", "x"), auth=None)
    assert r.status_code == 401


def test_wrong_auth_rejected(client):
    r = _post(client, _event("RENEWAL", "x"), auth="Bearer nope")
    assert r.status_code == 401


def test_not_configured_returns_503(client, monkeypatch, test_user):
    monkeypatch.setattr(
        "app.api.routes.webhooks.get_settings",
        lambda: _S(revenuecat_webhook_auth=None),
    )
    r = _post(client, _event("INITIAL_PURCHASE", test_user.id))
    assert r.status_code == 503


def test_initial_purchase_activates_subscription(client, db_session, test_user):
    r = _post(
        client,
        _event(
            "INITIAL_PURCHASE",
            test_user.id,
            product_id="plus_monthly",
            expiration_at_ms=4102444800000,  # 2100-01-01
        ),
    )
    assert r.status_code == 200
    sub = db_session.scalar(
        select(Subscription).where(Subscription.user_id == test_user.id)
    )
    assert sub.status == SubscriptionStatus.active
    assert sub.plan == "plus_monthly"
    assert sub.current_period_end.year == 2100


def test_expiration_downgrades(client, db_session, test_user):
    db_session.add(
        Subscription(
            user_id=test_user.id,
            status=SubscriptionStatus.active,
            provider="revenuecat",
        )
    )
    db_session.flush()

    r = _post(client, _event("EXPIRATION", test_user.id))
    assert r.status_code == 200
    sub = db_session.scalar(
        select(Subscription).where(Subscription.user_id == test_user.id)
    )
    assert sub.status == SubscriptionStatus.expired


def test_billing_issue_sets_grace(client, db_session, test_user):
    r = _post(client, _event("BILLING_ISSUE", test_user.id))
    assert r.status_code == 200
    sub = db_session.scalar(
        select(Subscription).where(Subscription.user_id == test_user.id)
    )
    assert sub.status == SubscriptionStatus.in_grace


def test_unknown_event_is_acked_without_change(client):
    r = _post(client, _event("SOME_FUTURE_EVENT", "abc"))
    assert r.status_code == 200
    assert r.json()["ignored"] == "SOME_FUTURE_EVENT"


def test_unmatched_user_is_acked(client):
    r = _post(client, _event("RENEWAL", "00000000-0000-0000-0000-000000000000"))
    assert r.status_code == 200
    assert r.json().get("unmatched") is True
