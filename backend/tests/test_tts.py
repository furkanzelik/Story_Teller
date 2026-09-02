"""Unit tests for TTS provider selection (no real synthesis)."""

import pytest

from app.core.config import Settings
from app.services.tts import (
    DisabledTTS,
    ElevenLabsTTS,
    PiperTTS,
    TTSError,
    build_tts_provider,
)


def _settings(**over) -> Settings:
    base = dict(
        anthropic_api_key=None,
        supabase_url=None,
        supabase_jwt_secret=None,
    )
    base.update(over)
    return Settings(**base)


def test_disabled_provider():
    p = build_tts_provider(_settings(tts_provider="disabled"))
    assert isinstance(p, DisabledTTS)
    with pytest.raises(TTSError):
        p.synthesize("hallo")


def test_elevenlabs_requires_credentials():
    with pytest.raises(TTSError):
        build_tts_provider(_settings(tts_provider="elevenlabs"))
    p = build_tts_provider(
        _settings(
            tts_provider="elevenlabs",
            elevenlabs_api_key="k",
            elevenlabs_voice_id="v",
        )
    )
    assert isinstance(p, ElevenLabsTTS)


def test_unknown_provider_raises():
    with pytest.raises(TTSError):
        build_tts_provider(_settings(tts_provider="robot"))


def test_piper_missing_voice_file_raises(tmp_path):
    with pytest.raises(TTSError):
        build_tts_provider(
            _settings(tts_provider="piper", piper_voices_dir=str(tmp_path))
        )


def test_piper_selected_when_voice_present(tmp_path):
    (tmp_path / "nl_NL-pim-medium.onnx").write_bytes(b"not-a-real-model")
    p = build_tts_provider(
        _settings(tts_provider="piper", piper_voices_dir=str(tmp_path))
    )
    assert isinstance(p, PiperTTS)
