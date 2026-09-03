import logging
from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_media_storage
from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Story, Subscription, SubscriptionStatus, User
from app.schemas import QuotaOut, SubscriptionOut, UserOut
from app.services.quota import get_quota_status
from app.services.storage import MediaStorage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    """Returns the signed-in parent, creating the local row on first call."""
    return user


@router.get("/me/subscription", response_model=SubscriptionOut)
def my_subscription(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SubscriptionOut:
    """Subscription status + this week's free-tier usage. The app polls this to
    render the counter and decide whether to show the paywall."""
    sub = db.scalar(select(Subscription).where(Subscription.user_id == user.id))
    quota = get_quota_status(db, user, get_settings())
    return SubscriptionOut(
        status=(sub.status if sub else SubscriptionStatus.free).value,
        plan=sub.plan if sub else None,
        quota=QuotaOut(
            unlimited=quota.unlimited,
            limit=quota.limit,
            used=quota.used,
            remaining=quota.remaining,
            resets_at=quota.resets_at,
        ),
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    storage: MediaStorage = Depends(get_media_storage),
) -> Response:
    """Permanently delete the account and all its data (App Store 5.1.1(v)).

    Removes local rows (stories, subscription, usage_events cascade via FK) and
    the cached audio files. Also deletes the Supabase auth user when
    `SUPABASE_SERVICE_KEY` is configured; otherwise that record is left for a
    separate cleanup and a warning is logged.
    """
    settings = get_settings()

    # Cached audio files for this user's stories.
    for (audio_url,) in db.execute(
        select(Story.audio_url).where(
            Story.user_id == user.id, Story.audio_url.is_not(None)
        )
    ):
        try:
            storage.delete(Path(audio_url).name)
        except Exception:  # best-effort
            logger.warning("could not delete media %s", audio_url)

    subject = user.auth_subject
    db.delete(user)  # stories / subscription / usage_events cascade
    db.commit()

    _delete_supabase_auth_user(settings, subject)
    logger.info("account deleted: %s", subject)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _delete_supabase_auth_user(settings, subject: str) -> None:
    if not (settings.supabase_url and settings.supabase_service_key):
        logger.warning(
            "SUPABASE_SERVICE_KEY not set — auth user %s left for cleanup", subject
        )
        return
    url = f"{settings.supabase_url.rstrip('/')}/auth/v1/admin/users/{subject}"
    try:
        resp = httpx.delete(
            url,
            headers={
                "apikey": settings.supabase_service_key,
                "Authorization": f"Bearer {settings.supabase_service_key}",
            },
            timeout=15,
        )
        if resp.status_code not in (200, 204, 404):
            logger.warning("supabase admin delete %s -> %s", subject, resp.status_code)
    except httpx.HTTPError as exc:
        logger.warning("supabase admin delete failed for %s: %s", subject, exc)
