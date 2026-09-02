from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models import User
from app.schemas import UserOut

router = APIRouter(tags=["me"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    """Returns the signed-in parent, creating the local row on first call."""
    return user
