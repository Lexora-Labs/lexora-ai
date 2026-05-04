"""Tests for Translate screen default output path naming."""

from pathlib import Path

import pytest

from lexora.ui.screens.translate import (
    _resolve_output_path_with_fallback,
    build_ui_default_output_file_path,
    provider_slug_for_output_filename,
    resolve_unique_output_path,
)


def test_provider_slug_uses_canonical_tokens() -> None:
    assert provider_slug_for_output_filename("OpenAI") == "openai"
    assert provider_slug_for_output_filename("Azure OpenAI") == "azure_openai"
    assert provider_slug_for_output_filename("Azure Foundry") == "azure_foundry"


def test_resolve_unique_output_path_adds_suffix(tmp_path: Path) -> None:
    target = tmp_path / "book_openai_vi.epub"
    target.write_text("a", encoding="utf-8")
    assert resolve_unique_output_path(target) == tmp_path / "book_openai_vi (1).epub"
    (tmp_path / "book_openai_vi (1).epub").write_text("b", encoding="utf-8")
    assert resolve_unique_output_path(target) == tmp_path / "book_openai_vi (2).epub"


def test_build_ui_default_output_file_path_under_library(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data_dir = tmp_path / "lexora-data"
    monkeypatch.setenv("LEXORA_DATA_DIR", str(data_dir))
    src = tmp_path / "samples" / "demo.epub"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(b"x")
    out = build_ui_default_output_file_path(str(src), "vi", "OpenAI")
    assert out.parent == data_dir / "library"
    assert out.name == "demo_openai_vi.epub"


def test_resolve_output_path_with_fallback_keeps_absolute_override(tmp_path: Path) -> None:
    default_path = tmp_path / "library" / "demo_openai_vi.epub"
    override = tmp_path / "custom" / "out.epub"
    resolved = _resolve_output_path_with_fallback(override=str(override), default_path=default_path)
    assert resolved == override


def test_resolve_output_path_with_fallback_maps_relative_override_to_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data_dir = tmp_path / "lexora-data"
    monkeypatch.setenv("LEXORA_DATA_DIR", str(data_dir))
    default_path = data_dir / "library" / "demo_openai_vi.epub"
    resolved = _resolve_output_path_with_fallback(override="relative-out.epub", default_path=default_path)
    assert resolved == data_dir / "library" / "relative-out.epub"
