from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Topic
from app.schemas import TopicOut

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut])
def list_topics(db: Session = Depends(get_db)) -> list[Topic]:
    stmt = (
        select(Topic)
        .where(Topic.is_active.is_(True))
        .order_by(Topic.sort_order, Topic.label)
    )
    return list(db.scalars(stmt))
