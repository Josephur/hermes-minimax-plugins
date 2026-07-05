"""MiniMax text-to-speech provider plugin for Hermes Agent."""

from __future__ import annotations

import asyncio
import json
import os
import queue
import threading
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from agent.tts_provider import TTSProvider


DEFAULT_BASE_URL = "https://api.minimax.io/v1/t2a_v2"
DEFAULT_WS_URL = "wss://api.minimax.io/ws/v1/t2a_v2"
DEFAULT_MODEL = "speech-2.8-hd"
DEFAULT_VOICE_ID = "English_expressive_narrator"
DEFAULT_SAMPLE_RATE = 32000
DEFAULT_BITRATE = 128000
SUPPORTED_FILE_FORMATS = {"mp3", "wav", "flac", "pcm"}
SUPPORTED_STREAM_FORMATS = {"mp3", "pcm", "flac"}


def _env_value(key: str, default: str = "") -> str:
    try:
        from hermes_cli.config import get_env_value

        value = get_env_value(key, default)
    except Exception:
        value = os.getenv(key, default)
    return value or default


def _load_tts_config() -> Dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        config = load_config()
    except Exception:
        return {}
    tts = config.get("tts") if isinstance(config, dict) else None
    return tts if isinstance(tts, dict) else {}


def _provider_config() -> Dict[str, Any]:
    tts = _load_tts_config()
    for key in ("minimax-tts", "minimax_tts", "minimax"):
        section = tts.get(key)
        if isinstance(section, dict):
            return section
    providers = tts.get("providers")
    if isinstance(providers, dict):
        section = providers.get("minimax-tts") or providers.get("minimax_tts")
        if isinstance(section, dict):
            return section
    return {}


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int_value(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _config_or_env(config: Dict[str, Any], key: str, env_key: str, default: Any) -> Any:
    value = config.get(key)
    if value not in (None, ""):
        return value
    return _env_value(env_key, str(default)) if env_key else default


def _with_group_id(url: str, group_id: str) -> str:
    if not group_id:
        return url
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("GroupId", group_id)
    return urlunparse(parsed._replace(query=urlencode(query)))


def _headers() -> Dict[str, str]:
    api_key = _env_value("MINIMAX_API_KEY")
    if not api_key:
        raise RuntimeError("MINIMAX_API_KEY is required for MiniMax TTS")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _resolve_options(
    *,
    voice: Optional[str],
    model: Optional[str],
    speed: Optional[float],
    format: str,
) -> Dict[str, Any]:
    config = _provider_config()
    group_id = str(
        config.get("group_id")
        or config.get("GroupId")
        or _env_value("MINIMAX_GROUP_ID")
        or ""
    ).strip()
    fmt = format or config.get("format") or config.get("output_format") or "mp3"
    fmt = str(fmt).lower().strip().lstrip(".")
    return {
        "base_url": _with_group_id(
            str(_config_or_env(config, "base_url", "MINIMAX_TTS_BASE_URL", DEFAULT_BASE_URL)),
            group_id,
        ),
        "ws_url": _with_group_id(
            str(_config_or_env(config, "ws_url", "MINIMAX_TTS_WS_URL", DEFAULT_WS_URL)),
            group_id,
        ),
        "model": model
        or str(_config_or_env(config, "model", "MINIMAX_TTS_MODEL", DEFAULT_MODEL)),
        "voice_id": voice
        or str(_config_or_env(config, "voice_id", "MINIMAX_TTS_VOICE_ID", DEFAULT_VOICE_ID)),
        "speed": speed if speed is not None else _float_value(config.get("speed"), 1.0),
        "vol": _float_value(config.get("vol", config.get("volume")), 1.0),
        "pitch": _int_value(config.get("pitch"), 0),
        "emotion": str(config.get("emotion") or "neutral"),
        "sample_rate": _int_value(config.get("sample_rate"), DEFAULT_SAMPLE_RATE),
        "bitrate": _int_value(config.get("bitrate"), DEFAULT_BITRATE),
        "format": fmt,
    }


def _payload(text: str, opts: Dict[str, Any], audio_format: str) -> Dict[str, Any]:
    return {
        "model": opts["model"],
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": opts["voice_id"],
            "speed": opts["speed"],
            "vol": opts["vol"],
            "pitch": opts["pitch"],
            "emotion": opts["emotion"],
        },
        "audio_setting": {
            "sample_rate": opts["sample_rate"],
            "bitrate": opts["bitrate"],
            "format": audio_format,
            "channel": 1,
        },
    }


class MiniMaxTTSProvider(TTSProvider):
    @property
    def name(self) -> str:
        return "minimax-tts"

    @property
    def display_name(self) -> str:
        return "MiniMax TTS"

    def is_available(self) -> bool:
        return bool(_env_value("MINIMAX_API_KEY"))

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "MiniMax TTS",
            "badge": "paid",
            "tag": "MiniMax system voices via speech-2.8; no voice cloning required",
            "env_vars": [
                {
                    "key": "MINIMAX_API_KEY",
                    "prompt": "MiniMax API key",
                    "url": "https://platform.minimax.io/",
                }
            ],
        }

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {"id": "speech-2.8-hd", "display": "Speech 2.8 HD", "max_text_length": 10000},
            {"id": "speech-2.8-turbo", "display": "Speech 2.8 Turbo", "max_text_length": 10000},
            {"id": "speech-2.6-hd", "display": "Speech 2.6 HD", "max_text_length": 10000},
            {"id": "speech-2.6-turbo", "display": "Speech 2.6 Turbo", "max_text_length": 10000},
            {"id": "speech-02-hd", "display": "Speech 02 HD", "max_text_length": 10000},
            {"id": "speech-02-turbo", "display": "Speech 02 Turbo", "max_text_length": 10000},
        ]

    def list_voices(self) -> List[Dict[str, Any]]:
        return [
            {"id": "English_expressive_narrator", "display": "English Expressive Narrator", "language": "en"},
            {"id": "English_Graceful_Lady", "display": "English Graceful Lady", "language": "en"},
            {"id": "English_Trustworth_Man", "display": "English Trustworthy Man", "language": "en"},
            {"id": "English_CalmWoman", "display": "English Calm Woman", "language": "en"},
            {"id": "English_ManWithDeepVoice", "display": "English Man With Deep Voice", "language": "en"},
        ]

    def default_model(self) -> str:
        return DEFAULT_MODEL

    def default_voice(self) -> str:
        return DEFAULT_VOICE_ID

    @property
    def voice_compatible(self) -> bool:
        return True

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        format: str = "mp3",
        **extra: Any,
    ) -> str:
        opts = _resolve_options(voice=voice, model=model, speed=speed, format=format)
        audio_format = opts["format"] if opts["format"] in SUPPORTED_FILE_FORMATS else "mp3"
        target = Path(output_path)
        if target.suffix.lower().lstrip(".") != audio_format:
            target = target.with_suffix(f".{audio_format}")
        target.parent.mkdir(parents=True, exist_ok=True)

        response = requests.post(
            opts["base_url"],
            headers=_headers(),
            json=_payload(text, opts, audio_format),
            timeout=_float_value(extra.get("timeout"), 120.0),
        )
        response.raise_for_status()
        data = response.json()
        base_resp = data.get("base_resp") or {}
        if int(base_resp.get("status_code", 0) or 0) != 0:
            raise RuntimeError(base_resp.get("status_msg") or "MiniMax TTS request failed")
        audio_hex = (data.get("data") or {}).get("audio")
        if not isinstance(audio_hex, str) or not audio_hex:
            raise RuntimeError(f"MiniMax TTS response did not include audio: {data}")
        target.write_bytes(bytes.fromhex(audio_hex))
        return str(target)

    def stream(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        format: str = "mp3",
        **extra: Any,
    ) -> Iterator[bytes]:
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError(
                "MiniMax streaming TTS requires the optional 'websockets' package. "
                "Normal synthesize() does not require it."
            ) from exc

        opts = _resolve_options(voice=voice, model=model, speed=None, format=format)
        audio_format = opts["format"] if opts["format"] in SUPPORTED_STREAM_FORMATS else "mp3"
        items: "queue.Queue[object]" = queue.Queue()
        sentinel = object()

        async def worker() -> None:
            try:
                async with websockets.connect(
                    opts["ws_url"],
                    additional_headers=_headers(),
                ) as websocket:
                    await websocket.recv()
                    await websocket.send(json.dumps({
                        "event": "task_start",
                        "model": opts["model"],
                        "voice_setting": {
                            "voice_id": opts["voice_id"],
                            "speed": opts["speed"],
                            "vol": opts["vol"],
                            "pitch": opts["pitch"],
                            "emotion": opts["emotion"],
                        },
                        "audio_setting": {
                            "sample_rate": opts["sample_rate"],
                            "bitrate": opts["bitrate"],
                            "format": audio_format,
                            "channel": 1,
                        },
                    }))
                    await websocket.recv()
                    await websocket.send(json.dumps({"event": "task_continue", "text": text}))
                    while True:
                        message = json.loads(await websocket.recv())
                        audio_hex = (message.get("data") or {}).get("audio")
                        if audio_hex:
                            items.put(bytes.fromhex(audio_hex))
                        if message.get("is_final"):
                            break
                    await websocket.send(json.dumps({"event": "task_finish"}))
            except BaseException as exc:  # noqa: BLE001
                items.put(exc)
            finally:
                items.put(sentinel)

        thread = threading.Thread(target=lambda: asyncio.run(worker()), daemon=True)
        thread.start()

        while True:
            item = items.get()
            if item is sentinel:
                break
            if isinstance(item, BaseException):
                raise item
            yield item  # type: ignore[misc]


def register(ctx) -> None:
    ctx.register_tts_provider(MiniMaxTTSProvider())
