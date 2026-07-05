"""MiniMax image generation backend for Hermes Agent.

Implements MiniMax's /v1/image_generation endpoint as an ImageGenProvider.
Text-only calls generate from the prompt. Calls that include image_url or
reference_image_urls use MiniMax's single subject_reference image path.
"""

from __future__ import annotations

import base64
import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    normalize_reference_images,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "image-01"
DEFAULT_BASE_URL = "https://api.minimax.io/v1/image_generation"
REQUEST_TIMEOUT = 180.0

_ASPECT_RATIOS = {
    "landscape": "16:9",
    "square": "1:1",
    "portrait": "9:16",
}

_MODELS: Dict[str, Dict[str, Any]] = {
    "image-01": {
        "display": "MiniMax Image-01",
        "speed": "varies",
        "strengths": "Text-to-image and single subject-reference generation",
    },
}


def _load_minimax_config() -> Dict[str, Any]:
    """Read image_gen.minimax from config.yaml, returning {} on failure."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        minimax = section.get("minimax") if isinstance(section, dict) else None
        return minimax if isinstance(minimax, dict) else {}
    except Exception as exc:  # noqa: BLE001 - config is best effort
        logger.debug("Could not load image_gen.minimax config: %s", exc)
        return {}


def _resolve_model(explicit: Optional[str] = None) -> str:
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    env_model = os.environ.get("MINIMAX_IMAGE_MODEL", "").strip()
    if env_model:
        return env_model
    cfg_model = _load_minimax_config().get("model")
    if isinstance(cfg_model, str) and cfg_model.strip():
        return cfg_model.strip()
    return DEFAULT_MODEL


def _resolve_endpoint() -> str:
    env_url = os.environ.get("MINIMAX_IMAGE_BASE_URL", "").strip()
    if env_url:
        return env_url
    cfg_url = _load_minimax_config().get("base_url")
    if isinstance(cfg_url, str) and cfg_url.strip():
        return cfg_url.strip()
    return DEFAULT_BASE_URL


def _image_ref_for_minimax(source: str) -> str:
    """Return a MiniMax-compatible image_file value.

    MiniMax accepts online image URLs in subject_reference. For local files, use
    a data URI so the request stays self-contained from Hermes' machine.
    """
    source = str(source or "").strip()
    if not source:
        raise ValueError("empty reference image")
    lower = source.lower()
    if lower.startswith(("http://", "https://", "data:")):
        return source

    from agent.file_safety import raise_if_read_blocked

    raise_if_read_blocked(source)
    path = Path(source).expanduser()
    raw = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


class MiniMaxImageGenProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "minimax"

    @property
    def display_name(self) -> str:
        return "MiniMax"

    def is_available(self) -> bool:
        return bool(os.environ.get("MINIMAX_API_KEY"))

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta.get("display", model_id),
                "speed": meta.get("speed", ""),
                "strengths": meta.get("strengths", ""),
            }
            for model_id, meta in _MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "MiniMax Image",
            "badge": "paid",
            "tag": "image-01 via MiniMax API; text-to-image and one reference image",
            "env_vars": [
                {
                    "key": "MINIMAX_API_KEY",
                    "prompt": "MiniMax API key",
                    "url": "https://platform.minimax.io/user-center/basic-information/interface-key",
                }
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "max_reference_images": 1,
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        api_key = os.environ.get("MINIMAX_API_KEY", "").strip()
        if not api_key:
            return error_response(
                error="MINIMAX_API_KEY is not set. Configure MiniMax in `hermes tools` or set MINIMAX_API_KEY.",
                error_type="missing_api_key",
                provider=self.name,
                aspect_ratio=aspect_ratio,
                prompt=prompt,
            )

        aspect = resolve_aspect_ratio(aspect_ratio)
        mm_aspect = _ASPECT_RATIOS.get(aspect, "16:9")
        model = _resolve_model(kwargs.get("model"))

        sources: List[str] = []
        if isinstance(image_url, str) and image_url.strip():
            sources.append(image_url.strip())
        refs = normalize_reference_images(reference_image_urls)
        if refs:
            sources.extend(refs)

        if len(sources) > 1:
            return error_response(
                error="MiniMax image generation supports only one reference image per request.",
                error_type="too_many_references",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "aspect_ratio": mm_aspect,
            "response_format": "base64",
        }
        modality = "text"
        if sources:
            try:
                image_file = _image_ref_for_minimax(sources[0])
            except Exception as exc:  # noqa: BLE001
                return error_response(
                    error=f"Could not load reference image for MiniMax: {exc}",
                    error_type="invalid_image_url",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
            payload["subject_reference"] = [
                {"type": "character", "image_file": image_file}
            ]
            modality = "image"

        headers = {"Authorization": f"Bearer {api_key}"}
        try:
            response = requests.post(
                _resolve_endpoint(),
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text[:300])
            except Exception:  # noqa: BLE001
                err_msg = resp.text[:300] if resp is not None else str(exc)
            logger.error("MiniMax image generation failed (%d): %s", status, err_msg)
            return error_response(
                error=f"MiniMax image generation failed ({status}): {err_msg}",
                error_type="api_error",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except requests.Timeout:
            return error_response(
                error=f"MiniMax image generation timed out ({int(REQUEST_TIMEOUT)}s)",
                error_type="timeout",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except requests.ConnectionError as exc:
            return error_response(
                error=f"MiniMax connection error: {exc}",
                error_type="connection_error",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            result = response.json()
        except Exception as exc:  # noqa: BLE001
            return error_response(
                error=f"MiniMax returned invalid JSON: {exc}",
                error_type="invalid_response",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        data = result.get("data") if isinstance(result, dict) else None
        images = data.get("image_base64") if isinstance(data, dict) else None
        if not isinstance(images, list) or not images:
            return error_response(
                error="MiniMax returned no image_base64 data",
                error_type="empty_response",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            saved_path = save_b64_image(images[0], prefix="minimax_image", extension="jpeg")
        except Exception as exc:  # noqa: BLE001
            return error_response(
                error=f"Could not save MiniMax image to cache: {exc}",
                error_type="io_error",
                provider=self.name,
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {}
        if len(images) > 1:
            extra["image_count"] = len(images)
        if isinstance(result, dict) and result.get("metadata"):
            extra["metadata"] = result["metadata"]

        return success_response(
            image=str(saved_path),
            model=model,
            prompt=prompt,
            aspect_ratio=aspect,
            provider=self.name,
            modality=modality,
            extra=extra,
        )


def register(ctx: Any) -> None:
    ctx.register_image_gen_provider(MiniMaxImageGenProvider())
