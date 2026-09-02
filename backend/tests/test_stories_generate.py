"""HTTP + DB tests for POST /stories/generate with a fake pipeline."""

import pytest
from sqlalchemy import select

from app.api.deps import get_story_pipeline
from app.main import app
from app.models import ModerationStatus, Story, Topic, UsageEvent
from app.services.story_pipeline import (
    PipelineResult,
    StoryModerationFailed,
    StoryServiceError,
)


@pytest.fixture
def topic(db_session):
    """The seeded "space" topic (get-or-create so tests work on a bare DB too)."""
    t = db_session.get(Topic, "space")
    if t is None:
        t = Topic(id="space", label="De ruimte", emoji="🚀", is_active=True)
        db_session.add(t)
        db_session.flush()
    return t


def _use_pipeline(fake):
    app.dependency_overrides[get_story_pipeline] = lambda: fake


class FakePipeline:
    def __init__(self, result=None, error=None):
        self._result = result
        self._error = error
        self.calls = 0

    def run(self, topic_label, age_group):
        self.calls += 1
        if self._error:
            raise self._error
        return self._result


def test_generate_happy_path_persists_story_and_usage(client, db_session, test_user, topic):
    _use_pipeline(
        FakePipeline(
            PipelineResult(
                title="De maanhaas",
                body="Er was eens een haas...",
                model="claude-haiku-4-5",
                moderation_note="approved",
                attempts=1,
            )
        )
    )
    r = client.post("/stories/generate", json={"topic_id": "space", "age_group": "4-5"})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "De maanhaas"
    assert data["topic_label"] == "De ruimte"
    assert data["audio_url"] is None

    story = db_session.scalar(select(Story).where(Story.user_id == test_user.id))
    assert story.moderation_status == ModerationStatus.approved
    assert story.llm_model == "claude-haiku-4-5"
    kinds = sorted(
        e.kind
        for e in db_session.scalars(
            select(UsageEvent).where(UsageEvent.user_id == test_user.id)
        )
    )
    assert kinds == ["generation_attempt", "story_generated"]


def test_generate_moderation_failure_returns_422_and_audit_row(
    client, db_session, test_user, topic
):
    _use_pipeline(FakePipeline(error=StoryModerationFailed("rejected [violence]: mes", 2)))
    r = client.post("/stories/generate", json={"topic_id": "space", "age_group": "6-7"})
    assert r.status_code == 422

    story = db_session.scalar(select(Story).where(Story.user_id == test_user.id))
    assert story.moderation_status == ModerationStatus.rejected
    assert "violence" in story.moderation_notes
    # The attempt is metered; no successful-generation event.
    kinds = [
        e.kind
        for e in db_session.scalars(
            select(UsageEvent).where(UsageEvent.user_id == test_user.id)
        )
    ]
    assert kinds == ["generation_attempt"]


def test_generate_service_error_returns_502(client, topic):
    _use_pipeline(FakePipeline(error=StoryServiceError("upstream 529")))
    r = client.post("/stories/generate", json={"topic_id": "space", "age_group": "4-5"})
    assert r.status_code == 502


def test_generate_unknown_topic_returns_404(client):
    _use_pipeline(FakePipeline())
    r = client.post("/stories/generate", json={"topic_id": "nope", "age_group": "4-5"})
    assert r.status_code == 404


def test_generate_free_text_topic_not_allowed_yet(client):
    _use_pipeline(FakePipeline())
    r = client.post("/stories/generate", json={"topic_text": "draken", "age_group": "4-5"})
    assert r.status_code == 400


def test_generate_invalid_age_group_422(client, topic):
    _use_pipeline(FakePipeline())
    r = client.post("/stories/generate", json={"topic_id": "space", "age_group": "20-30"})
    assert r.status_code == 422
