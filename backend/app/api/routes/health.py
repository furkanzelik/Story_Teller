from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas import HealthOut

router = APIRouter(tags=["meta"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    settings = get_settings()
    return HealthOut(status="ok", environment=settings.environment)
