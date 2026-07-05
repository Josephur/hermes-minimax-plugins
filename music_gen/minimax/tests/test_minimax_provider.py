import importlib.util
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1] / "__init__.py"


def load_plugin():
    spec = importlib.util.spec_from_file_location("minimax_music_plugin", PLUGIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_catalog_defaults():
    module = load_plugin()
    provider = module.MinimaxMusicGenProvider()
    assert provider.name == "minimax"
    assert provider.default_model() == "music-2.6-free"
    assert any(m["id"] == "music-cover" for m in provider.list_models())


def test_cover_requires_reference_url(monkeypatch):
    module = load_plugin()
    provider = module.MinimaxMusicGenProvider()
    result = provider.generate("jazz cover", model="music-cover-free")
    assert result["success"] is False
    assert result["error_type"] == "validation"
