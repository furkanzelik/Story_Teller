"""Shared FastAPI dependencies for Fase 2.

Kept separate from the route modules so tests can override
`get_story_pipeline` with a fake and never touch the Anthropic API.
"""

from __future__ import annotations

from functools import lru_cache

import anthropic
from fastapi import HTTPException, status

from app.core.config import get_settings
from app.services.llm import AnthropicStoryService
from app.services.moderation import AnthropicModerationService
from app.services.storage import LocalMediaStorage, MediaStorage
from app.services.story_pipeline import StoryPipeline
from app.services.tts import TTSError, TTSProvider, build_tts_provider


@lru_cache
def _anthropic_client() -> anthropic.Anthropic | None:
    key = get_settings().anthropic_api_key
    if not key:
        return None
    # Extra retries (with the SDK's exponential backoff) to ride out short
    # `overloaded_error` (529) spikes on Anthropic's side.
    return anthropic.Anthropic(api_key=key, max_retries=4)


def get_story_pipeline() -> StoryPipeline:
    settings = get_settings()
    client = _anthropic_client()
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verhaalgeneratie is niet geconfigureerd (ANTHROPIC_API_KEY).",
        )
    return StoryPipeline(
        story_service=AnthropicStoryService(client, settings.story_model),
        moderation_service=AnthropicModerationService(
            client, settings.moderation_model
        ),
        max_attempts=1 + settings.story_regeneration_attempts,
    )


@lru_cache
def get_media_storage() -> MediaStorage:
    return LocalMediaStorage(get_settings().media_dir)


def get_tts_provider() -> TTSProvider:
    try:
        return build_tts_provider(get_settings())
    except TTSError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Voorleesaudio is niet beschikbaar: {exc}",
        ) from exc
