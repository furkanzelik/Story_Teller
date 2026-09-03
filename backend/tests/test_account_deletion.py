"""DELETE /me — account + data removal (App Store 5.1.1(v))."""

import pytest
from sqlalchemy import select

from app.api.deps import get_media_storage
from app.main import app
from app.models import (
    ModerationStatus,
    Story,
    Subscription,
    SubscriptionStatus,
    UsageEvent,
    User,
)


class FakeStorage:
    def __init__(self):
        self.files = {"keep.mp3": b"x"}

    def exists(self, name):
        return name in self.files

    def save(self, name, data):
        self.files[name] = data

    def delete(self, name):
        self.files.pop(name, None)

    def url_path(self, name):
        return f"/media/{name}"


@pytest.fixture
def storage():
    s = FakeStorage()
    app.dependency_overrides[get_media_storage] = lambda: s
    yield s
    app.dependency_overrides.pop(get_media_storage, None)


@pytest.fixture(autouse=True)
def _no_supabase(monkeypatch):
    # No service key -> the endpoint skips the Supabase admin call.
    from dataclasses import dataclass

    @dataclass
    class _S:
        supabase_url: str | None = None
        supabase_service_key: str | None = None

    monkeypatch.setattr("app.api.routes.me.get_settings", lambda: _S())


def test_delete_account_removes_all_user_data(client, db_session, test_user, storage):
    uid = test_user.id
    db_session.add_all([
        Story(
            user_id=uid,
            topic_label="x",
            age_group="4-5",
            title="t",
            body="b",
            moderation_status=ModerationStatus.approved,
            is_saved=True,
            audio_url="/media/story1.mp3",
        ),
        Subscription(user_id=uid, status=SubscriptionStatus.free, provider="revenuecat"),
        UsageEvent(user_id=uid, kind="story_generated"),
    ])
    storage.files["story1.mp3"] = b"audio"
    db_session.flush()

    r = client.delete("/me")
    assert r.status_code == 204

    assert db_session.get(User, uid) is None
    assert db_session.scalars(
        select(Story).where(Story.user_id == uid)
    ).all() == []
    assert db_session.scalars(
        select(UsageEvent).where(UsageEvent.user_id == uid)
    ).all() == []
    assert db_session.scalars(
        select(Subscription).where(Subscription.user_id == uid)
    ).all() == []
    # Audio for the deleted story is gone; unrelated files untouched.
    assert "story1.mp3" not in storage.files
    assert "keep.mp3" in storage.files
