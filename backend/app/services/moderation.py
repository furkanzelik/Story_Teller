"""Moderation stack (Fase 2 stap 7) — the project's hard requirement 1.

`moderate()` combines the local blocklist with a Claude classifier call and
returns a single verdict. It fails **closed**: any error → not approved, so a
Claude outage can never let an unchecked story through.
"""

from __future__ import annotations

import logging

import anthropic
from pydantic import BaseModel, Field

from app.services.blocklist import find_blocked_terms
from app.services.prompts import (
    MODERATION_SYSTEM,
    build_moderation_user_prompt,
)

logger = logging.getLogger(__name__)


class ModerationResult(BaseModel):
    approved: bool
    categories: list[str] = Field(default_factory=list)
    reason: str | None = None

    def note(self) -> str:
        if self.approved:
            return "approved"
        cats = ", ".join(self.categories) or "unspecified"
        return f"rejected [{cats}]: {self.reason or ''}".strip()


class AnthropicModerationService:
    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    def moderate(
        self, title: str, body: str, topic_label: str, age_group: str
    ) -> ModerationResult:
        blocked = find_blocked_terms(title, body)
        if blocked:
            return ModerationResult(
                approved=False,
                categories=["blocklist"],
                reason="Geblokkeerde termen: " + ", ".join(blocked),
            )

        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=600,
                system=MODERATION_SYSTEM,
                messages=[
                    {
                        "role": "user",
                        "content": build_moderation_user_prompt(
                            title, body, topic_label, age_group
                        ),
                    }
                ],
                output_format=ModerationResult,
            )
        except anthropic.APIError as exc:
            logger.warning("Moderation call failed, failing closed: %s", exc)
            return ModerationResult(
                approved=False,
                categories=["moderation_error"],
                reason="Moderatiecontrole is tijdelijk niet beschikbaar.",
            )

        result = getattr(response, "parsed_output", None) or getattr(
            response, "parsed", None
        )
        if not isinstance(result, ModerationResult):
            logger.warning("Moderation returned unparseable output, failing closed")
            return ModerationResult(
                approved=False,
                categories=["moderation_error"],
                reason="Moderatie-antwoord kon niet gelezen worden.",
            )
        # A model that says approved=true but still lists categories is a
        # contradiction — treat as not approved.
        if result.approved and result.categories:
            result.approved = False
        return result
