"""initial schema: users, topics, stories, subscriptions, usage_events

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-01

Hand-written to match app/models.py. After bringing up your database run
`alembic revision --autogenerate -m "verify"` once — it should produce an
empty migration, confirming this file and the models agree.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False: the types are created/dropped explicitly in
# upgrade()/downgrade() so create_table() does not emit a duplicate CREATE TYPE.
moderation_status = postgresql.ENUM(
    "pending", "approved", "rejected",
    name="moderation_status", create_type=False,
)
subscription_status = postgresql.ENUM(
    "free", "active", "in_grace", "expired",
    name="subscription_status", create_type=False,
)

_ts = sa.text("now()")


def upgrade() -> None:
    moderation_status.create(op.get_bind(), checkfirst=True)
    subscription_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "topics",
        sa.Column("id", sa.String(48), primary_key=True),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("emoji", sa.String(16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=_ts, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=_ts, nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("auth_provider", sa.String(32), nullable=False),
        sa.Column("auth_subject", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=_ts, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=_ts, nullable=False),
        sa.UniqueConstraint("auth_provider", "auth_subject", name="uq_user_auth"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_auth_subject", "users", ["auth_subject"])

    op.create_table(
        "stories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "topic_id",
            sa.String(48),
            sa.ForeignKey("topics.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("topic_label", sa.String(160), nullable=False),
        sa.Column("age_group", sa.String(16), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "moderation_status",
            moderation_status,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("moderation_notes", sa.Text(), nullable=True),
        sa.Column("llm_model", sa.String(80), nullable=True),
        sa.Column("audio_url", sa.String(1024), nullable=True),
        sa.Column("audio_voice", sa.String(80), nullable=True),
        sa.Column("is_saved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=_ts, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=_ts, nullable=False),
    )
    op.create_index("ix_stories_user_id", "stories", ["user_id"])
    op.create_index("ix_stories_is_saved", "stories", ["is_saved"])
    op.create_index(
        "ix_stories_moderation_status", "stories", ["moderation_status"]
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "status", subscription_status, nullable=False, server_default="free"
        ),
        sa.Column("plan", sa.String(64), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("provider_customer_id", sa.String(255), nullable=True),
        sa.Column(
            "current_period_end", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(), server_default=_ts, nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=_ts, nullable=False),
    )

    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(48), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=_ts,
            nullable=False,
        ),
    )
    op.create_index("ix_usage_events_user_id", "usage_events", ["user_id"])
    op.create_index("ix_usage_events_created_at", "usage_events", ["created_at"])


def downgrade() -> None:
    op.drop_table("usage_events")
    op.drop_table("subscriptions")
    op.drop_table("stories")
    op.drop_table("users")
    op.drop_table("topics")
    bind = op.get_bind()
    subscription_status.drop(bind, checkfirst=True)
    moderation_status.drop(bind, checkfirst=True)
