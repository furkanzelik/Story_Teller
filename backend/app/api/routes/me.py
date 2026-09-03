from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import Subscription, SubscriptionStatus, User
from app.schemas import QuotaOut, SubscriptionOut, UserOut
from app.services.quota import get_quota_status

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
