"""Generate → moderate → (regenerate once) orchestration for Fase 2 stap 6-8."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.services.llm import AnthropicStoryService, StoryServiceError
from app.services.moderation import AnthropicModerationService

logger = logging.getLogger(__name__)

__all__ = [
    "StoryPipeline",
    "PipelineResult",
    "StoryModerationFailed",
    "StoryServiceError",
]


@dataclass(frozen=True)
class PipelineResult:
    title: str
    body: str
    model: str
    moderation_note: str
    attempts: int


class StoryModerationFailed(RuntimeError):
    """Every attempt was rejected by the moderation check."""

    def __init__(self, note: str, attempts: int) -> None:
        super().__init__(f"moderation rejected all {attempts} attempt(s): {note}")
        self.note = note
        self.attempts = attempts


class StoryPipeline:
    def __init__(
        self,
        story_service: AnthropicStoryService,
        moderation_service: AnthropicModerationService,
        max_attempts: int = 2,
    ) -> None:
        self._story = story_service
        self._moderation = moderation_service
        self._max_attempts = max(1, max_attempts)

    def run(self, topic_label: str, age_group: str) -> PipelineResult:
        last_note = "no attempts made"
        for attempt in range(1, self._max_attempts + 1):
            story = self._story.generate(topic_label, age_group)  # StoryServiceError
            verdict = self._moderation.moderate(
                story.title, story.body, topic_label, age_group
            )
            if verdict.approved:
                return PipelineResult(
                    title=story.title,
                    body=story.body,
                    model=story.model,
                    moderation_note=verdict.note(),
                    attempts=attempt,
                )
            last_note = verdict.note()
            logger.info(
                "story attempt %d/%d rejected: %s",
                attempt,
                self._max_attempts,
                last_note,
            )
        raise StoryModerationFailed(last_note, self._max_attempts)
