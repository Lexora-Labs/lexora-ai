from pathlib import Path

from lexora.cli import DEFAULT_GLOBAL_CACHE_PATH
from lexora.ui.screens.translate import _normalize_ui_cache_path


def test_normalize_ui_cache_path_rejects_relative_legacy_path() -> None:
    assert _normalize_ui_cache_path(".lexora/translation_cache.jsonl") == DEFAULT_GLOBAL_CACHE_PATH


def test_normalize_ui_cache_path_keeps_absolute_path(tmp_path: Path) -> None:
    absolute = tmp_path / "cache" / "custom.jsonl"
    assert _normalize_ui_cache_path(str(absolute)) == str(absolute)

