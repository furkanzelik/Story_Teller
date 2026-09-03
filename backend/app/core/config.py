from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment / .env.

    Only the keys needed for Fase 1 are wired up. LLM / TTS / auth keys get
    added in their respective phases; keep them here so there is a single
    source of truth.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Verhaaltjesmaker API"
    # Production-safe defaults: local dev flips these on via backend/.env.
    environment: str = "production"
    debug: bool = False
    # Expose /docs, /redoc, /openapi.json (auto-on in non-production).
    enable_docs: bool = False

    # Abuse limits per user per hour (independent of the Fase 5 free-tier quota).
    generation_rate_limit_per_hour: int = 20
    audio_rate_limit_per_hour: int = 40

    # --- subscription / free tier (Fase 5) ---
    # Stories a non-subscriber can generate per calendar week (Mon 00:00 UTC).
    free_stories_per_week: int = 2
    # RevenueCat -> Project -> Webhooks -> Authorization header value.
    revenuecat_webhook_auth: str | None = None

    # postgresql+psycopg://user:pass@host:5432/dbname
    database_url: str = (
        "postgresql+psycopg://storyteller:storyteller@localhost:5432/storyteller"
    )

    # Comma-separated list of origins allowed to call the API.
    # The Flutter web build and local tooling; native apps ignore CORS.
    cors_origins: str = "http://localhost,http://localhost:3000,http://localhost:8080"

    # --- auth (Fase 1 stap 4) ---
    supabase_url: str | None = None
    # Project Settings -> API -> JWT Settings -> "JWT Secret" (HS256).
    # When unset, auth-protected endpoints return 503 instead of trusting
    # unverified tokens.
    supabase_jwt_secret: str | None = None
    supabase_jwt_audience: str = "authenticated"
    # Secret API key (sb_secret_… / legacy service_role). Only used to also
    # delete the Supabase auth user on account deletion; local data is wiped
    # regardless. Keep this out of the app and out of git.
    supabase_service_key: str | None = None

    # --- story generation + moderation (Fase 2) ---
    # console.anthropic.com -> API keys. When unset, /stories/generate
    # returns 503 instead of pretending to work.
    anthropic_api_key: str | None = None
    story_model: str = "claude-haiku-4-5"
    moderation_model: str = "claude-haiku-4-5"
    # How many extra tries after the first if the story fails moderation.
    story_regeneration_attempts: int = 1

    # --- voorleesaudio / TTS (Fase 3) ---
    tts_provider: str = "piper"              # "piper" | "elevenlabs" | "disabled"
    tts_length_scale: float = 1.15           # >1 = slower, calmer (bedtime)
    # Piper (free, offline): voice .onnx lives in this dir as <voice>.onnx
    piper_voice: str = "nl_NL-pim-medium"
    piper_voices_dir: str = "voices"
    # ElevenLabs (paid, wired but off by default)
    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None
    elevenlabs_model: str = "eleven_multilingual_v2"
    # Where generated audio is cached.
    media_dir: str = "media"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_dev(self) -> bool:
        return self.environment != "production"

    @property
    def docs_enabled(self) -> bool:
        return self.enable_docs or self.is_dev


@lru_cache
def get_settings() -> Settings:
    return Settings()
