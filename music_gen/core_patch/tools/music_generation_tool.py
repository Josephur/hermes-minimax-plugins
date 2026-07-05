#!/usr/bin/env python3
"""Music Generation Tool."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from agent.music_gen_provider import MAX_LYRICS_CHARS, MAX_PROMPT_CHARS, error_response
from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

MUSIC_GENERATE_SCHEMA: Dict[str, Any] = {
    "name": "music_generate",
    "description": "Generate a song or instrumental track using the configured music generation backend. Returns MEDIA:<local_path> in the audio field.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Music style, mood, genre, instrumentation, vocal style, or cover style."},
            "lyrics": {"type": "string", "description": "Optional lyrics with section tags like [Verse] and [Chorus]."},
            "is_instrumental": {"type": "boolean", "description": "Generate an instrumental-only original track."},
            "duration_seconds": {"type": "integer", "description": "Desired duration in seconds. Providers may ignore or clamp."},
            "model": {"type": "string", "description": "Optional model override for the active provider."},
            "reference_audio_url": {"type": "string", "description": "Public HTTPS reference audio URL for cover models."},
        },
        "required": [],
    },
}


def _read_music_gen_section() -> Dict[str, Any]:
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        section = cfg.get("music_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not read music_gen config: %s", exc)
        return {}


def _configured_provider() -> Optional[str]:
    value = _read_music_gen_section().get("provider")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _configured_model() -> Optional[str]:
    value = _read_music_gen_section().get("model")
    return value.strip() if isinstance(value, str) and value.strip() else None


def check_music_generation_requirements() -> bool:
    try:
        from agent.music_gen_registry import list_providers
        from hermes_cli.plugins import _ensure_plugins_discovered
        _ensure_plugins_discovered()
        return any(p.is_available() for p in list_providers())
    except Exception:
        return False


def _resolve_active_provider():
    try:
        from agent.music_gen_registry import get_active_provider
        from hermes_cli.plugins import _ensure_plugins_discovered
        _ensure_plugins_discovered()
        provider = get_active_provider()
        if provider is None:
            _ensure_plugins_discovered(force=True)
            provider = get_active_provider()
        return provider
    except Exception as exc:
        logger.debug("music_gen provider resolution failed: %s", exc)
        return None


def _handle_music_generate(args: Dict[str, Any], **_kw: Any) -> str:
    prompt = (args.get("prompt") or "").strip()
    lyrics = (args.get("lyrics") or "").strip() or None
    reference_audio_url = (args.get("reference_audio_url") or "").strip() or None
    model_override = (args.get("model") or "").strip() or None
    is_instrumental = bool(args.get("is_instrumental", False))
    duration = args.get("duration_seconds")
    try:
        duration = int(duration) if duration not in (None, "") else None
    except (TypeError, ValueError):
        duration = None

    if prompt and len(prompt) > MAX_PROMPT_CHARS:
        return tool_error(f"prompt is too long; max {MAX_PROMPT_CHARS} characters")
    if lyrics and len(lyrics) > MAX_LYRICS_CHARS:
        return tool_error(f"lyrics is too long; max {MAX_LYRICS_CHARS} characters")

    provider = _resolve_active_provider()
    configured = _configured_provider()
    if provider is None:
        msg = "No music generation backend is configured. Run `hermes tools` -> Music Generation to pick one."
        if configured:
            msg = f"music_gen.provider='{configured}' is configured but no plugin registered that name."
        return json.dumps(error_response(error=msg, error_type="no_provider_configured", provider=configured or ""))

    model = model_override or _configured_model() or provider.default_model()
    try:
        result = provider.generate(
            prompt=prompt,
            lyrics=lyrics,
            is_instrumental=is_instrumental,
            duration_seconds=duration,
            model=model,
            reference_audio_url=reference_audio_url,
        )
    except Exception as exc:
        return json.dumps(error_response(
            error=f"Provider '{getattr(provider, 'name', '?')}' error: {exc}",
            error_type="provider_exception",
            provider=getattr(provider, "name", ""),
            model=model or "",
            prompt=prompt,
        ))
    if not isinstance(result, dict):
        return json.dumps(error_response(error="Provider returned a non-dict result", error_type="provider_contract", provider=getattr(provider, "name", ""), model=model or "", prompt=prompt))
    return json.dumps(result)


def _build_dynamic_music_schema() -> Dict[str, Any]:
    parts = [MUSIC_GENERATE_SCHEMA["description"]]
    configured = _configured_provider()
    if configured:
        parts.append(f"Active backend: {configured}.")
    return {"description": "\n".join(parts)}


registry.register(
    name="music_generate",
    toolset="music_gen",
    schema=MUSIC_GENERATE_SCHEMA,
    handler=_handle_music_generate,
    check_fn=check_music_generation_requirements,
    requires_env=[],
    is_async=False,
    emoji="♪",
    dynamic_schema_overrides=_build_dynamic_music_schema,
)
