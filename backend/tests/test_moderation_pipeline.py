"""Pure-unit tests for the moderation stack — no DB, no HTTP, no Anthropic."""

import pytest

from app.services.blocklist import find_blocked_terms
from app.services.llm import GeneratedStory, StoryServiceError
from app.services.moderation import ModerationResult
from app.services.story_pipeline import StoryModerationFailed, StoryPipeline


class FakeStoryService:
    def __init__(self, drafts):
        self._drafts = list(drafts)
        self.calls = 0

    def generate(self, topic_label, age_group):
        self.calls += 1
        item = self._drafts.pop(0)
        if isinstance(item, Exception):
            raise item
        return GeneratedStory(title=item[0], body=item[1], model="fake")


class FakeModeration:
    def __init__(self, verdicts):
        self._verdicts = list(verdicts)
        self.calls = 0

    def moderate(self, title, body, topic_label, age_group):
        self.calls += 1
        return self._verdicts.pop(0)


_OK = ModerationResult(approved=True)
_BAD = ModerationResult(approved=False, categories=["scary_or_threatening"], reason="eng")


def test_blocklist_flags_violent_terms():
    hits = find_blocked_terms("De draak had een pistool", "alles was rustig")
    assert "pistool" in hits


def test_blocklist_ignores_clean_text():
    assert find_blocked_terms("De vos en de haas dronken thee in het bos") == []


def test_pipeline_returns_first_approved_story():
    story = FakeStoryService([("Titel", "Body")])
    mod = FakeModeration([_OK])
    result = StoryPipeline(story, mod, max_attempts=2).run("ruimte", "4-5")
    assert result.attempts == 1
    assert result.title == "Titel"
    assert story.calls == 1 and mod.calls == 1


def test_pipeline_regenerates_once_then_succeeds():
    story = FakeStoryService([("Slecht", "eng verhaal"), ("Goed", "lief verhaal")])
    mod = FakeModeration([_BAD, _OK])
    result = StoryPipeline(story, mod, max_attempts=2).run("ruimte", "4-5")
    assert result.attempts == 2
    assert result.title == "Goed"
    assert story.calls == 2 and mod.calls == 2


def test_pipeline_raises_when_all_attempts_rejected():
    story = FakeStoryService([("A", "a"), ("B", "b")])
    mod = FakeModeration([_BAD, _BAD])
    with pytest.raises(StoryModerationFailed) as exc:
        StoryPipeline(story, mod, max_attempts=2).run("ruimte", "4-5")
    assert exc.value.attempts == 2
    assert "scary_or_threatening" in exc.value.note


def test_pipeline_propagates_generation_error():
    story = FakeStoryService([StoryServiceError("boom")])
    mod = FakeModeration([])
    with pytest.raises(StoryServiceError):
        StoryPipeline(story, mod, max_attempts=2).run("ruimte", "4-5")


def test_moderation_result_note_is_readable():
    assert _BAD.note() == "rejected [scary_or_threatening]: eng"
    assert _OK.note() == "approved"
