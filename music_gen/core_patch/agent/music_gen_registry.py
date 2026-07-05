"""Music Generation Provider Registry."""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from agent.music_gen_provider import MusicGenProvider

logger = logging.getLogger(__name__)
_providers: Dict[str, MusicGenProvider] = {}
_lock = threading.Lock()


def register_provider(provider: MusicGenProvider) -> None:
    if not isinstance(provider, MusicGenProvider):
        raise TypeError(f"register_provider() expects MusicGenProvider, got {type(provider).__name__}")
    name = provider.name
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Music gen provider .name must be a non-empty string")
    key = name.strip()
    with _lock:
        existing = _providers.get(key)
        _providers[key] = provider
    if existing is not None:
        logger.debug("Music gen provider '%s' re-registered", key)
    else:
        logger.debug("Registered music gen provider '%s'", key)


def list_providers() -> List[MusicGenProvider]:
    with _lock:
        items = list(_providers.values())
    return sorted(items, key=lambda p: p.name)


def get_provider(name: str) -> Optional[MusicGenProvider]:
    if not isinstance(name, str):
        return None
    with _lock:
        return _providers.get(name.strip())


def get_active_provider() -> Optional[MusicGenProvider]:
    configured = None
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        section = cfg.get("music_gen") if isinstance(cfg, dict) else None
        if isinstance(section, dict) and isinstance(section.get("provider"), str):
            configured = section["provider"].strip() or None
    except Exception as exc:
        logger.debug("Could not read music_gen.provider: %s", exc)
    with _lock:
        snapshot = dict(_providers)
    if configured and configured in snapshot:
        return snapshot[configured]
    available = []
    for provider in snapshot.values():
        try:
            if provider.is_available():
                available.append(provider)
        except Exception:
            continue
    if len(available) == 1:
        return available[0]
    return None


def _reset_for_tests() -> None:
    with _lock:
        _providers.clear()
