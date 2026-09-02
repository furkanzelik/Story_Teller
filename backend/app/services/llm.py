"""Story generation via Claude (Fase 2 stap 6)."""

from __future__ import annotations

import json
import logging

import anthropic
from pydantic import BaseModel, Field

from app.services.prompts import (
    STORY_SYSTEM,
    build_story_user_prompt,
)

logger = logging.getLogger(__name__)


class StoryDraft(BaseModel):
    title: str = Field(max_length=160)
    body: str


class GeneratedStory(BaseModel):
    title: str
    body: str
    model: str


class StoryServiceError(RuntimeError):
    """Generation failed (API error, refusal, or unparseable output)."""


class AnthropicStoryService:
    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    def generate(self, topic_label: str, age_group: str) -> GeneratedStory:
        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=3000,
                system=STORY_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": build_story_user_prompt(topic_label, age_group),
                    }
                ],
                output_format=StoryDraft,
            )
        except anthropic.APIError as exc:  # network, rate limit, 5xx, bad request
            raise StoryServiceError(f"Claude call failed: {exc}") from exc

        if response.stop_reason == "refusal":
            raise StoryServiceError("Claude refused to generate this story")

        draft = _extract_draft(response)
        title = draft.title.strip()
        body = draft.body.strip()
        if not title or not body:
            raise StoryServiceError("Claude returned an empty story")
        return GeneratedStory(title=title, body=body, model=self._model)


def _extract_draft(response: object) -> StoryDraft:
    """`messages.parse` returns the validated model on `.parsed_output` (SDK
    versions differ: also try `.parsed`); fall back to parsing the text block."""
    for attr in ("parsed_output", "parsed"):
        parsed = getattr(response, attr, None)
        if isinstance(parsed, StoryDraft):
            return parsed
        if parsed is not None:
            return StoryDraft.model_validate(parsed)

    text = next(
        (b.text for b in getattr(response, "content", []) if getattr(b, "type", None) == "text"),
        None,
    )
    if not text:
        raise StoryServiceError("No parseable content in Claude response")
    try:
        return StoryDraft.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValueError) as exc:
        raise StoryServiceError(f"Could not parse story JSON: {exc}") from exc
