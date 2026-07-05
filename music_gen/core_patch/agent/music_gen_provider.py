"""Music Generation Provider ABC for Hermes Agent."""

from __future__ import annotations

import abc
import base64
import datetime
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_FORMAT = "mp3"
DEFAULT_SAMPLE_RATE = 44100
DEFAULT_BITRATE = 256000
MAX_PROMPT_CHARS = 2000
MAX_LYRICS_CHARS = 1000
VALID_SAMPLE_RATES = {16000, 24000, 32000, 44100}
VALID_BITRATES = {32000, 64000, 128000, 256000}


class MusicGenProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Stable provider id used in music_gen.provider."""

    @property
    def display_name(self) -> str:
        return self.name.title()

    def is_available(self) -> bool:
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return []

    def get_setup_schema(self) -> Dict[str, Any]:
        return {"name": self.display_name, "badge": "", "tag": "", "env_vars": []}

    def default_model(self) -> Optional[str]:
        models = self.list_models()
        if models:
            return models[0].get("id")
        return None

    def capabilities(self) -> Dict[str, Any]:
        return {
            "supports_lyrics": True,
            "supports_instrumental": True,
            "supports_cover": False,
            "max_prompt_chars": MAX_PROMPT_CHARS,
            "max_lyrics_chars": MAX_LYRICS_CHARS,
            "output_formats": [DEFAULT_OUTPUT_FORMAT],
        }

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        lyrics: Optional[str] = None,
        is_instrumental: bool = False,
        duration_seconds: Optional[int] = None,
        model: Optional[str] = None,
        reference_audio_url: Optional[str] = None,
        output_path: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate music and return success_response() or error_response()."""


def _music_cache_dir() -> Path:
    from hermes_constants import get_hermes_home

    path = get_hermes_home() / "cache" / "music"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_path(prefix: str = "music", extension: str = DEFAULT_OUTPUT_FORMAT) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:8]
    return _music_cache_dir() / f"{prefix}_{ts}_{short}.{extension.lstrip('.')}"


def save_b64_audio(b64_data: str, *, prefix: str = "music", extension: str = DEFAULT_OUTPUT_FORMAT) -> Path:
    path = cache_path(prefix=prefix, extension=extension)
    path.write_bytes(base64.b64decode(b64_data))
    return path


def save_bytes_audio(raw: bytes, *, prefix: str = "music", extension: str = DEFAULT_OUTPUT_FORMAT) -> Path:
    path = cache_path(prefix=prefix, extension=extension)
    path.write_bytes(raw)
    return path


def media_ref(path_or_url: str) -> str:
    return path_or_url if path_or_url.startswith("MEDIA:") else f"MEDIA:{path_or_url}"


def success_response(
    *,
    audio: str,
    model: str,
    prompt: str,
    provider: str,
    lyrics: str = "",
    duration_seconds: int = 0,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    bitrate: int = DEFAULT_BITRATE,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "success": True,
        "audio": media_ref(audio),
        "model": model,
        "prompt": prompt,
        "lyrics": lyrics,
        "duration_seconds": duration_seconds,
        "sample_rate": sample_rate,
        "bitrate": bitrate,
        "provider": provider,
    }
    if extra:
        result.update(extra)
    return result


def error_response(
    *,
    error: str,
    error_type: str = "provider_error",
    provider: str = "",
    model: str = "",
    prompt: str = "",
) -> Dict[str, Any]:
    return {
        "success": False,
        "audio": None,
        "model": model,
        "prompt": prompt,
        "provider": provider,
        "error": error,
        "error_type": error_type,
    }
