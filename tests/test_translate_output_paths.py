"""Tests for Translate screen default output path naming."""

from pathlib import Path

import pytest

from lexora.ui.screens.translate import (
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
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "samples" / "demo.epub"
    src.parent.mkdir(parents=True, exist_ok=True)
    src.write_bytes(b"x")
    out = build_ui_default_output_file_path(str(src), "vi", "OpenAI")
    assert out.parent == tmp_path / "library"
    assert out.name == "demo_openai_vi.epub"
