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
    environment: str = "development"
    debug: bool = True

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
    # Where generated audio is cached + how the app reaches it.
    media_dir: str = "media"
    # Public base URL for media; when None it's built from the request host.
    media_base_url: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
