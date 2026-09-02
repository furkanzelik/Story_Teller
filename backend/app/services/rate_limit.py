"""Per-user rate limiting backed by the `usage_events` table.

DB-backed (not in-memory) so it holds across multiple workers / instances.
Independent of the Fase 5 free-tier business quota — this one only exists to
stop a compromised or abusive account from hammering the paid LLM / the CPU.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import UsageEvent


def enforce_rate_limit(
    db: Session,
    user_id,
    *,
    kind: str,
    limit: int,
    window: timedelta = timedelta(hours=1),
) -> None:
    """Raise 429 if the user logged >= `limit` events of `kind` within `window`."""
    since = datetime.now(UTC) - window
    count = db.scalar(
        select(func.count())
        .select_from(UsageEvent)
        .where(
            UsageEvent.user_id == user_id,
            UsageEvent.kind == kind,
            UsageEvent.created_at >= since,
        )
    )
    if (count or 0) >= limit:
        retry_after = int(window.total_seconds())
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Je hebt even te veel verhaaltjes gemaakt. Probeer het later opnieuw.",
            headers={"Retry-After": str(retry_after)},
        )
