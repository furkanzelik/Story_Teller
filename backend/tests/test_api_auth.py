"""API-level auth guard tests that do not need a database.

The DB-backed path (user upsert on first valid token) is exercised once
PostgreSQL is available; see backend/README.md.
"""

from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@dataclass
class _FakeSettings:
    supabase_jwt_secret: str | None = None
    supabase_url: str | None = None
    supabase_jwt_audience: str = "authenticated"


def test_me_requires_auth_when_configured(monkeypatch):
    monkeypatch.setattr(
        "app.core.security.get_settings",
        lambda: _FakeSettings(supabase_jwt_secret="s"),
    )
    r = client.get("/me")
    assert r.status_code == 401


def test_me_503_when_auth_not_configured(monkeypatch):
    monkeypatch.setattr(
        "app.core.security.get_settings",
        lambda: _FakeSettings(),
    )
    r = client.get("/me")
    assert r.status_code == 503


def test_stories_list_requires_auth(monkeypatch):
    monkeypatch.setattr(
        "app.core.security.get_settings",
        lambda: _FakeSettings(supabase_jwt_secret="s"),
    )
    r = client.get("/stories")
    assert r.status_code == 401


def test_health_is_public():
    assert client.get("/health").status_code == 200
