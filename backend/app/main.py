from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import health, me, stories, topics
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    # Hide the interactive docs / schema outside dev.
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # No cookies are used — the JWT rides in the Authorization header.
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router)
app.include_router(me.router)
app.include_router(topics.router)
app.include_router(stories.router)

# Cached read-aloud audio (Fase 3). Local disk for dev; swap for object
# storage in production (see services/storage.py).
_media_dir = Path(settings.media_dir)
_media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=_media_dir), name="media")


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {"service": settings.app_name, "docs": "/docs"}
