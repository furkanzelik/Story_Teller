import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_media_storage, get_story_pipeline, get_tts_provider
from app.core.security import get_current_user
from app.db.session import get_db
from app.models import ModerationStatus, Story, Topic, UsageEvent, User
from app.schemas import AudioOut, GenerateStoryIn, SetSavedIn, StoryOut
from app.services.prompts import AGE_BANDS
from app.services.storage import MediaStorage
from app.services.story_pipeline import (
    StoryModerationFailed,
    StoryPipeline,
    StoryServiceError,
)
from app.services.tts import TTSError, TTSProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("", response_model=list[StoryOut])
def list_stories(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Story]:
    """The signed-in parent's saved library. Only moderation-approved stories."""
    stmt = (
        select(Story)
        .where(
            Story.user_id == user.id,
            Story.is_saved.is_(True),
            Story.moderation_status == ModerationStatus.approved,
        )
        .order_by(Story.created_at.desc())
    )
    return list(db.scalars(stmt))


@router.post(
    "/generate", response_model=StoryOut, status_code=status.HTTP_201_CREATED
)
def generate_story(
    payload: GenerateStoryIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    pipeline: StoryPipeline = Depends(get_story_pipeline),
) -> Story:
    """topic + age -> prompt -> Claude -> moderation check -> persist.

    The story is only returned (and stored as `approved`) once it passes the
    moderation stack; a run that fails every attempt is stored as `rejected`
    for auditing and answered with 422.
    """
    topic_id, topic_label = _resolve_topic(db, payload)

    if payload.age_group not in AGE_BANDS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Ongeldige leeftijdsgroep.",
        )

    try:
        result = pipeline.run(topic_label, payload.age_group)
    except StoryModerationFailed as exc:
        db.add(
            Story(
                user_id=user.id,
                topic_id=topic_id,
                topic_label=topic_label,
                age_group=payload.age_group,
                title="",
                body="",
                moderation_status=ModerationStatus.rejected,
                moderation_notes=exc.note,
            )
        )
        db.commit()
        logger.info("generation rejected for user %s: %s", user.id, exc.note)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="We konden geen passend verhaaltje maken. Kies een ander onderwerp.",
        ) from exc
    except StoryServiceError as exc:
        logger.warning("story service error for user %s: %s", user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="De verhaaltjesmaker is even niet bereikbaar. Probeer het zo nog eens.",
        ) from exc

    story = Story(
        user_id=user.id,
        topic_id=topic_id,
        topic_label=topic_label,
        age_group=payload.age_group,
        title=result.title,
        body=result.body,
        moderation_status=ModerationStatus.approved,
        moderation_notes=result.moderation_note,
        llm_model=result.model,
    )
    db.add(story)
    db.add(UsageEvent(user_id=user.id, kind="story_generated"))
    db.commit()
    db.refresh(story)
    return story


@router.get("/{story_id}", response_model=StoryOut)
def get_story(
    story_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Story:
    """A single story owned by the caller (used when reopening from the library)."""
    return _get_owned_story(db, story_id, user, require_approved=True)


@router.put("/{story_id}/saved", response_model=StoryOut)
def set_story_saved(
    story_id: uuid.UUID,
    payload: SetSavedIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Story:
    """Add the story to / remove it from the parent's library (Fase 4 stap 12)."""
    story = _get_owned_story(db, story_id, user, require_approved=True)
    story.is_saved = payload.saved
    db.commit()
    db.refresh(story)
    return story


@router.post("/{story_id}/audio", response_model=AudioOut)
def story_audio(
    story_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    tts: TTSProvider = Depends(get_tts_provider),
    storage: MediaStorage = Depends(get_media_storage),
) -> AudioOut:
    """Generate (once) and return the read-aloud audio for a story.

    Cached: a second call returns the stored file. The app calls this right
    after the story text renders, so the text is never blocked on TTS.
    """
    story = _get_owned_story(db, story_id, user, require_approved=True)

    if story.audio_url and storage.exists(Path(story.audio_url).name):
        return AudioOut(audio_url=story.audio_url)

    try:
        result = tts.synthesize(story.body)
    except TTSError as exc:
        logger.warning("tts failed for story %s: %s", story_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Het voorlezen lukte niet. Probeer het opnieuw.",
        ) from exc

    name = f"{story_id}.{result.ext}"
    storage.save(name, result.audio)
    story.audio_url = storage.url_path(name)
    story.audio_voice = result.voice
    db.commit()
    return AudioOut(audio_url=story.audio_url)


def _get_owned_story(
    db: Session, story_id: uuid.UUID, user: User, *, require_approved: bool
) -> Story:
    """Fetch a story that belongs to `user`, or 404. Central IDOR check:
    a story owned by someone else is indistinguishable from a missing one."""
    story = db.get(Story, story_id)
    if story is None or story.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Verhaal niet gevonden."
        )
    if require_approved and story.moderation_status != ModerationStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dit verhaal is niet goedgekeurd.",
        )
    return story


def _resolve_topic(db: Session, payload: GenerateStoryIn) -> tuple[str | None, str]:
    if payload.topic_id:
        topic = db.get(Topic, payload.topic_id)
        if topic is None or not topic.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Onbekend onderwerp.",
            )
        return topic.id, topic.label
    if payload.topic_text:
        # Free-text topics widen the moderation surface — Fase 5, behind the
        # parental gate.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eigen onderwerpen kunnen nog niet.",
        )
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Kies een onderwerp.",
    )
