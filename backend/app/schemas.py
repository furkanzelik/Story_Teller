from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: str = "ok"
    environment: str
    version: str = "0.1.0"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None = None


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    emoji: str


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    body: str
    topic_label: str
    topic_id: str | None = None
    age_group: str
    audio_url: str | None = None
    is_saved: bool = False
    created_at: datetime


class AudioOut(BaseModel):
    # Relative path like "/media/<uuid>.mp3"; the app prepends its API base URL.
    audio_url: str


class SetSavedIn(BaseModel):
    saved: bool


class QuotaOut(BaseModel):
    unlimited: bool
    limit: int
    used: int
    remaining: int
    resets_at: datetime


class SubscriptionOut(BaseModel):
    status: str          # "free" | "active" | "in_grace" | "expired"
    plan: str | None = None
    quota: QuotaOut


class GenerateStoryIn(BaseModel):
    """Request body for Fase 2. Kept here so the contract is visible now."""

    topic_id: str | None = Field(
        default=None, description="Slug from GET /topics; null for free text"
    )
    topic_text: str | None = Field(
        default=None, max_length=120, description="Free-text topic (Fase 5)"
    )
    age_group: str = Field(examples=["4-5", "6-7"])
