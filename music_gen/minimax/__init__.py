"""MiniMax music generation backend for Hermes Agent."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    from agent.music_gen_provider import (
        DEFAULT_BITRATE,
        DEFAULT_OUTPUT_FORMAT,
        DEFAULT_SAMPLE_RATE,
        MusicGenProvider,
        cache_path,
        error_response,
        success_response,
    )
except ImportError:  # Stock Hermes before music_gen lands.
    MusicGenProvider = object  # type: ignore[misc,assignment]

    def error_response(**kwargs):
        return {"success": False, **kwargs}

    def success_response(**kwargs):
        return {"success": True, **kwargs}

    DEFAULT_BITRATE = 256000
    DEFAULT_OUTPUT_FORMAT = "mp3"
    DEFAULT_SAMPLE_RATE = 44100

    def cache_path(prefix: str = "music", extension: str = "mp3") -> Path:
        import tempfile, uuid
        return Path(tempfile.gettempdir()) / f"{prefix}_{uuid.uuid4().hex[:8]}.{extension}"

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "music-2.6-free"
DEFAULT_BASE_URL = "https://api.minimax.io/v1/music_generation"
MODELS: Dict[str, Dict[str, Any]] = {
    "music-2.6": {"display": "Music 2.6", "tier": "paid", "instrumental": True, "cover": False},
    "music-2.6-free": {"display": "Music 2.6 Free", "tier": "free", "instrumental": True, "cover": False},
    "music-cover": {"display": "Music Cover", "tier": "paid", "instrumental": False, "cover": True},
    "music-cover-free": {"display": "Music Cover Free", "tier": "free", "instrumental": False, "cover": True},
}
ERROR_TYPES = {1002: "rate_limit", 1004: "auth_failed", 1008: "insufficient_balance"}


def _env_value(key: str, default: str = "") -> str:
    try:
        from hermes_cli.config import get_env_value
        return get_env_value(key, default) or default
    except Exception:
        return os.getenv(key, default) or default


def _load_music_config() -> Dict[str, Any]:
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        section = cfg.get("music_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception:
        return {}


def _provider_config() -> Dict[str, Any]:
    cfg = _load_music_config()
    section = cfg.get("minimax")
    return section if isinstance(section, dict) else {}


def _headers() -> Dict[str, str]:
    api_key = _env_value("MINIMAX_API_KEY")
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY is required for MiniMax Music Generation")
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def _resolve_model(model: Optional[str]) -> str:
    cfg = _provider_config()
    candidates = [model, os.getenv("MINIMAX_MUSIC_MODEL"), cfg.get("model"), _load_music_config().get("model"), DEFAULT_MODEL]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip() in MODELS:
            return candidate.strip()
    return DEFAULT_MODEL


def _extract_audio_url(data: Dict[str, Any]) -> Optional[str]:
    stack: List[Any] = [data]
    keys = {"audio", "audio_url", "music_url", "url", "download_url", "file_url"}
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                if k in keys and isinstance(v, str) and v.startswith(("http://", "https://")):
                    return v
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return None


def _base_resp_error(data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    base = data.get("base_resp") or {}
    if not isinstance(base, dict):
        return None
    code = int(base.get("status_code", 0) or 0)
    if code == 0:
        return None
    return {"type": ERROR_TYPES.get(code, "api_error"), "message": base.get("status_msg") or f"MiniMax API error {code}"}


def _download_audio(url: str, *, model: str, prompt: str, extension: str = DEFAULT_OUTPUT_FORMAT) -> Path:
    digest = hashlib.sha256(f"{model}\0{prompt}\0{url}".encode("utf-8")).hexdigest()[:16]
    target = cache_path(prefix=f"minimax_music_{digest}", extension=extension)
    response = requests.get(url, timeout=180)
    response.raise_for_status()
    target.write_bytes(response.content)
    return target


class MinimaxMusicGenProvider(MusicGenProvider):
    @property
    def name(self) -> str:
        return "minimax"

    @property
    def display_name(self) -> str:
        return "MiniMax Music"

    def is_available(self) -> bool:
        return bool(_env_value("MINIMAX_API_KEY"))

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "MiniMax Music",
            "badge": "paid/free tiers",
            "tag": "Music 2.6 originals and cover generation",
            "env_vars": [{"key": "MINIMAX_API_KEY", "prompt": "MiniMax API key", "url": "https://platform.minimax.io/"}],
        }

    def list_models(self) -> List[Dict[str, Any]]:
        return [{"id": k, **v} for k, v in MODELS.items()]

    def default_model(self) -> str:
        return DEFAULT_MODEL

    def capabilities(self) -> Dict[str, Any]:
        return {
            "supports_lyrics": True,
            "supports_instrumental": True,
            "supports_cover": True,
            "models": list(MODELS),
            "output_formats": ["mp3"],
            "max_prompt_chars": 2000,
            "max_lyrics_chars": 1000,
        }

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
        model_id = _resolve_model(model)
        meta = MODELS[model_id]
        prompt = (prompt or "").strip()
        lyrics = (lyrics or "").strip()
        is_cover = bool(meta.get("cover"))

        if is_cover:
            if not reference_audio_url or not reference_audio_url.startswith(("http://", "https://")):
                return error_response(error="reference_audio_url is required for MiniMax cover models", error_type="validation", provider=self.name, model=model_id, prompt=prompt)
            if is_instrumental:
                return error_response(error="is_instrumental is not supported for MiniMax cover models", error_type="validation", provider=self.name, model=model_id, prompt=prompt)
        elif not prompt and not lyrics:
            return error_response(error="prompt or lyrics is required for MiniMax original music models", error_type="validation", provider=self.name, model=model_id, prompt=prompt)

        cfg = _provider_config()
        sample_rate = int(cfg.get("sample_rate", DEFAULT_SAMPLE_RATE) or DEFAULT_SAMPLE_RATE)
        bitrate = int(cfg.get("bitrate", DEFAULT_BITRATE) or DEFAULT_BITRATE)
        fmt = str(cfg.get("format", DEFAULT_OUTPUT_FORMAT) or DEFAULT_OUTPUT_FORMAT).lower()
        base_url = str(cfg.get("base_url") or _env_value("MINIMAX_MUSIC_BASE_URL", DEFAULT_BASE_URL))

        payload: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt,
            "audio_setting": {"sample_rate": sample_rate, "bitrate": bitrate, "format": fmt},
            "output_format": "url",
        }
        if lyrics:
            payload["lyrics"] = lyrics
        if not is_cover:
            payload["is_instrumental"] = bool(is_instrumental)
        if is_cover:
            payload["audio_url"] = reference_audio_url
        if duration_seconds:
            payload["duration_seconds"] = int(duration_seconds)

        response = requests.post(base_url, headers=_headers(), json=payload, timeout=240)
        response.raise_for_status()
        data = response.json()
        api_error = _base_resp_error(data)
        if api_error:
            return error_response(error=api_error["message"], error_type=api_error["type"], provider=self.name, model=model_id, prompt=prompt)
        audio_url = _extract_audio_url(data)
        if not audio_url:
            return error_response(error=f"MiniMax response did not include an audio URL: {data}", error_type="bad_response", provider=self.name, model=model_id, prompt=prompt)
        local = Path(output_path) if output_path else _download_audio(audio_url, model=model_id, prompt=prompt or lyrics, extension=fmt)
        if output_path:
            dl = requests.get(audio_url, timeout=180)
            dl.raise_for_status()
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(dl.content)
        return success_response(
            audio=str(local),
            model=model_id,
            prompt=prompt,
            lyrics=lyrics,
            provider=self.name,
            duration_seconds=int(((data.get("extra_info") or {}).get("music_duration") or 0) / 1000) or int(duration_seconds or 0),
            sample_rate=int((data.get("extra_info") or {}).get("music_sample_rate") or sample_rate),
            bitrate=int((data.get("extra_info") or {}).get("bitrate") or bitrate),
            extra={"local_path": str(local), "source_url": audio_url, "size_bytes": local.stat().st_size, "is_cover": is_cover},
        )


def register(ctx) -> None:
    if MusicGenProvider is object:
        try:
            import logging
            logging.getLogger(__name__).warning("MiniMax Music plugin installed, but Hermes core has no music_gen support yet. Apply music_gen/core_patch first.")
        finally:
            return
    ctx.register_music_gen_provider(MinimaxMusicGenProvider())
