"""Fase 4 — save/unsave + single-story fetch, incl. IDOR checks."""

import uuid

import pytest
from sqlalchemy import select

from app.models import ModerationStatus, Story, User


def _story(user_id, **over) -> Story:
    data = dict(
        user_id=user_id,
        topic_label="De ruimte",
        age_group="4-5",
        title="Luna",
        body="Er was eens een sterretje.",
        moderation_status=ModerationStatus.approved,
    )
    data.update(over)
    return Story(**data)


@pytest.fixture
def other_user(db_session) -> User:
    u = User(email="other@example.com", auth_provider="supabase", auth_subject="other")
    db_session.add(u)
    db_session.flush()
    return u


@pytest.fixture
def my_story(db_session, test_user) -> Story:
    s = _story(test_user.id)
    db_session.add(s)
    db_session.flush()
    return s


def test_save_then_unsave_toggles_library(client, db_session, test_user, my_story):
    assert client.get("/stories").json() == []

    r = client.put(f"/stories/{my_story.id}/saved", json={"saved": True})
    assert r.status_code == 200
    assert r.json()["is_saved"] is True

    lib = client.get("/stories").json()
    assert [s["id"] for s in lib] == [str(my_story.id)]

    r = client.put(f"/stories/{my_story.id}/saved", json={"saved": False})
    assert r.status_code == 200
    assert client.get("/stories").json() == []


def test_get_single_owned_story(client, my_story):
    r = client.get(f"/stories/{my_story.id}")
    assert r.status_code == 200
    assert r.json()["title"] == "Luna"


def test_cannot_read_another_users_story(client, db_session, other_user):
    theirs = _story(other_user.id, title="Geheim")
    db_session.add(theirs)
    db_session.flush()

    assert client.get(f"/stories/{theirs.id}").status_code == 404
    assert (
        client.put(f"/stories/{theirs.id}/saved", json={"saved": True}).status_code
        == 404
    )
    # And it was not mutated.
    db_session.refresh(theirs)
    assert theirs.is_saved is False


def test_get_missing_story_is_404(client):
    assert client.get(f"/stories/{uuid.uuid4()}").status_code == 404


def test_cannot_save_a_rejected_story(client, db_session, test_user):
    bad = _story(test_user.id, moderation_status=ModerationStatus.rejected, title="", body="")
    db_session.add(bad)
    db_session.flush()
    assert (
        client.put(f"/stories/{bad.id}/saved", json={"saved": True}).status_code == 409
    )


def test_library_excludes_other_users_saved_stories(
    client, db_session, test_user, other_user
):
    mine = _story(test_user.id, is_saved=True, title="Van mij")
    theirs = _story(other_user.id, is_saved=True, title="Van hen")
    db_session.add_all([mine, theirs])
    db_session.flush()

    titles = [s["title"] for s in client.get("/stories").json()]
    assert titles == ["Van mij"]
