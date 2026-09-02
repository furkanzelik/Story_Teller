"""Where generated audio files live (Fase 3 stap 10).

Local disk for dev, served by FastAPI's StaticFiles at `/media`. The `MediaStorage`
interface keeps the swap to Supabase Storage / S3 small later.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class MediaStorage(Protocol):
    def exists(self, name: str) -> bool: ...
    def save(self, name: str, data: bytes) -> None: ...
    def url_path(self, name: str) -> str: ...


class LocalMediaStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        # `name` is server-controlled ("<uuid>.mp3"); guard anyway.
        safe = Path(name).name
        return self._root / safe

    def exists(self, name: str) -> bool:
        return self._path(name).is_file()

    def save(self, name: str, data: bytes) -> None:
        self._path(name).write_bytes(data)

    def url_path(self, name: str) -> str:
        return f"/media/{Path(name).name}"
