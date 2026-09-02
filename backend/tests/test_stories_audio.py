"""HTTP + DB tests for POST /stories/{id}/audio with a fake TTS provider."""

import uuid

import pytest

from app.api.deps import get_media_storage, get_tts_provider
from app.main import app
from app.models import ModerationStatus, Story
from app.services.tts import TTSError, TTSResult


class FakeTTS:
    def __init__(self, error: Exception | None = None):
        self.error = error
        self.calls = 0

    def synthesize(self, text: str) -> TTSResult:
        self.calls += 1
        if self.error:
            raise self.error
        return TTSResult(audio=b"ID3fake-mp3", ext="mp3", voice="test-voice")


class FakeStorage:
    def __init__(self):
        self.files: dict[str, bytes] = {}

    def exists(self, name: str) -> bool:
        return name in self.files

    def save(self, name: str, data: bytes) -> None:
        self.files[name] = data

    def url_path(self, name: str) -> str:
        return f"/media/{name}"


@pytest.fixture
def story(db_session, test_user):
    s = Story(
        user_id=test_user.id,
        topic_label="De ruimte",
        age_group="4-5",
        title="Luna",
        body="Er was eens een sterretje. Rust nu. Je bent veilig.",
        moderation_status=ModerationStatus.approved,
        moderation_notes="approved",
    )
    db_session.add(s)
    db_session.flush()
    return s


def _override(tts, storage):
    app.dependency_overrides[get_tts_provider] = lambda: tts
    app.dependency_overrides[get_media_storage] = lambda: storage


def test_audio_generated_cached_and_persisted(client, db_session, story):
    tts, storage = FakeTTS(), FakeStorage()
    _override(tts, storage)

    r1 = client.post(f"/stories/{story.id}/audio")
    assert r1.status_code == 200, r1.text
    url = r1.json()["audio_url"]
    assert url == f"/media/{story.id}.mp3"
    assert storage.files[f"{story.id}.mp3"] == b"ID3fake-mp3"

    db_session.refresh(story)
    assert story.audio_url == url
    assert story.audio_voice == "test-voice"

    # Second call is served from cache — no second synthesis.
    r2 = client.post(f"/stories/{story.id}/audio")
    assert r2.status_code == 200
    assert tts.calls == 1


def test_audio_404_for_other_users_story(client, story):
    _override(FakeTTS(), FakeStorage())
    r = client.post(f"/stories/{uuid.uuid4()}/audio")
    assert r.status_code == 404


def test_audio_409_when_story_not_approved(client, db_session, test_user):
    rejected = Story(
        user_id=test_user.id,
        topic_label="x",
        age_group="4-5",
        title="",
        body="",
        moderation_status=ModerationStatus.rejected,
    )
    db_session.add(rejected)
    db_session.flush()
    _override(FakeTTS(), FakeStorage())

    r = client.post(f"/stories/{rejected.id}/audio")
    assert r.status_code == 409


def test_audio_502_when_tts_fails(client, story):
    _override(FakeTTS(error=TTSError("piper boom")), FakeStorage())
    r = client.post(f"/stories/{story.id}/audio")
    assert r.status_code == 502
