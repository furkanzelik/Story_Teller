"""Text-to-speech for the read-aloud audio (Fase 3 stap 9-10).

Provider-agnostic: `TTSResult` carries the audio bytes + container format, and
`build_tts_provider(settings)` picks the implementation from config. Piper
(free, offline, Dutch) is the default; ElevenLabs is wired but only used when
`TTS_PROVIDER=elevenlabs` and a key is set.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import wave
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol

import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class TTSError(RuntimeError):
    """Synthesis failed."""


@dataclass(frozen=True)
class TTSResult:
    audio: bytes
    ext: str          # "mp3" | "wav"
    voice: str


class TTSProvider(Protocol):
    def synthesize(self, text: str) -> TTSResult: ...


# --- Piper (default) -------------------------------------------------------

@lru_cache(maxsize=4)
def _load_piper_voice(onnx_path: str):
    from piper import PiperVoice  # imported lazily; heavy dependency

    return PiperVoice.load(onnx_path)


_FFMPEG = shutil.which("ffmpeg")


def _wav_to_mp3(wav_bytes: bytes) -> bytes | None:
    if not _FFMPEG:
        return None
    try:
        proc = subprocess.run(
            [_FFMPEG, "-hide_banner", "-loglevel", "error",
             "-i", "pipe:0", "-codec:a", "libmp3lame", "-qscale:a", "4",
             "-f", "mp3", "pipe:1"],
            input=wav_bytes, capture_output=True, timeout=120,
        )
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
        logger.warning("ffmpeg mp3 conversion failed: %s", proc.stderr[:400])
    except (subprocess.SubprocessError, OSError) as exc:
        logger.warning("ffmpeg unavailable at runtime: %s", exc)
    return None


class PiperTTS:
    def __init__(self, onnx_path: Path, voice_name: str, length_scale: float) -> None:
        if not onnx_path.exists():
            raise TTSError(
                f"Piper voice not found: {onnx_path} "
                f"(download <voice>.onnx + .onnx.json into that folder)"
            )
        self._onnx_path = str(onnx_path)
        self._voice_name = voice_name
        self._length_scale = length_scale

    def synthesize(self, text: str) -> TTSResult:
        from piper.config import SynthesisConfig

        try:
            voice = _load_piper_voice(self._onnx_path)
            cfg = SynthesisConfig(length_scale=self._length_scale)
            with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
                with wave.open(tmp, "wb") as wf:
                    voice.synthesize_wav(text, wf, syn_config=cfg)
                tmp.seek(0)
                wav_bytes = tmp.read()
        except Exception as exc:  # onnxruntime / piper raise plain exceptions
            raise TTSError(f"Piper synthesis failed: {exc}") from exc

        mp3 = _wav_to_mp3(wav_bytes)
        if mp3:
            return TTSResult(audio=mp3, ext="mp3", voice=self._voice_name)
        return TTSResult(audio=wav_bytes, ext="wav", voice=self._voice_name)


# --- ElevenLabs (paid, opt-in) ------------------------------------------------

class ElevenLabsTTS:
    def __init__(self, api_key: str, voice_id: str, model: str) -> None:
        self._api_key = api_key
        self._voice_id = voice_id
        self._model = model

    def synthesize(self, text: str) -> TTSResult:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}"
        try:
            resp = httpx.post(
                url,
                headers={"xi-api-key": self._api_key, "accept": "audio/mpeg"},
                json={"text": text, "model_id": self._model},
                timeout=120,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise TTSError(f"ElevenLabs request failed: {exc}") from exc
        return TTSResult(audio=resp.content, ext="mp3", voice=self._voice_id)


# --- selection --------------------------------------------------------------

class DisabledTTS:
    def synthesize(self, text: str) -> TTSResult:  # noqa: ARG002
        raise TTSError("TTS is disabled (TTS_PROVIDER=disabled).")


def build_tts_provider(settings: Settings) -> TTSProvider:
    provider = (settings.tts_provider or "piper").lower()
    if provider == "disabled":
        return DisabledTTS()
    if provider == "elevenlabs":
        if not (settings.elevenlabs_api_key and settings.elevenlabs_voice_id):
            raise TTSError("ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID not set.")
        return ElevenLabsTTS(
            settings.elevenlabs_api_key,
            settings.elevenlabs_voice_id,
            settings.elevenlabs_model,
        )
    if provider == "piper":
        onnx = Path(settings.piper_voices_dir) / f"{settings.piper_voice}.onnx"
        return PiperTTS(onnx, settings.piper_voice, settings.tts_length_scale)
    raise TTSError(f"Unknown TTS_PROVIDER: {provider!r}")
