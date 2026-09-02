"""SQLAlchemy ORM models for Fase 1 stap 3.

Tables: users, topics, stories, subscriptions, usage_events.

Design notes
------------
* Auth is parent-only. A `users` row is created on first sign-in (Fase 1 stap 4)
  keyed by the auth provider's subject id; there is no separate child account.
* `stories.moderation_status` is the gate the hard-requirements demand: the API
  never returns a story to the client unless it is `approved`. The column lives
  in the schema now so Fase 2 only has to fill it in.
* `topics` is seeded from a fixed catalogue but kept in the DB so the list can
  grow without an app release. Free-text topics (Fase 5) will store
  `topic_id = NULL` and only the snapshotted `topic_label`.
* `usage_events` is the raw feed for the free-tier limit (2 stories / rolling
  week). Counting events keeps the rule easy to change later.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


def _uuid_col() -> Mapped[uuid.UUID]:
    return mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class ModerationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SubscriptionStatus(str, enum.Enum):
    free = "free"
    active = "active"
    in_grace = "in_grace"
    expired = "expired"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("auth_provider", "auth_subject", name="uq_user_auth"),
    )

    id: Mapped[uuid.UUID] = _uuid_col()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    auth_provider: Mapped[str] = mapped_column(String(32), default="supabase")
    auth_subject: Mapped[str] = mapped_column(String(255), index=True)
    display_name: Mapped[str | None] = mapped_column(String(120))

    stories: Mapped[list["Story"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    subscription: Mapped["Subscription | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class Topic(TimestampMixin, Base):
    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)  # slug
    label: Mapped[str] = mapped_column(String(120))
    emoji: Mapped[str] = mapped_column(String(16), default="✨")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Story(TimestampMixin, Base):
    __tablename__ = "stories"

    id: Mapped[uuid.UUID] = _uuid_col()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    topic_id: Mapped[str | None] = mapped_column(
        String(48), ForeignKey("topics.id", ondelete="SET NULL")
    )
    # Snapshot so history survives topic edits / free-text prompts.
    topic_label: Mapped[str] = mapped_column(String(160))
    age_group: Mapped[str] = mapped_column(String(16))  # "4-5", "6-7", ...

    title: Mapped[str] = mapped_column(String(200), default="")
    body: Mapped[str] = mapped_column(Text, default="")

    moderation_status: Mapped[ModerationStatus] = mapped_column(
        Enum(ModerationStatus, name="moderation_status"),
        default=ModerationStatus.pending,
        index=True,
    )
    moderation_notes: Mapped[str | None] = mapped_column(Text)

    llm_model: Mapped[str | None] = mapped_column(String(80))
    audio_url: Mapped[str | None] = mapped_column(String(1024))
    audio_voice: Mapped[str | None] = mapped_column(String(80))

    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    user: Mapped["User | None"] = relationship(back_populates="stories")
    topic: Mapped["Topic | None"] = relationship()


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = _uuid_col()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status"),
        default=SubscriptionStatus.free,
    )
    plan: Mapped[str | None] = mapped_column(String(64))  # "plus_monthly"
    provider: Mapped[str] = mapped_column(String(32), default="revenuecat")
    provider_customer_id: Mapped[str | None] = mapped_column(String(255))
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    user: Mapped["User"] = relationship(back_populates="subscription")


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[uuid.UUID] = _uuid_col()
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(48), default="story_generated")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
