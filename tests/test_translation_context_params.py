"""Tests for translation context (tone, domain, instruction) system message and cache inputs."""

import hashlib

import pytest

from lexora.core.base_translator import (
    TranslationConfig,
    TranslationMode,
    build_system_message,
    compose_neighbor_context_system_instruction,
    normalize_domain,
    normalize_tone,
)


def _baseline_only() -> str:
    return (
        "You are a professional literary translator. "
        "Translate faithfully, fluently, and maintain formatting where possible. "
        "Do not add explanations or notes. Output only the translation."
    )


def test_build_system_message_defaults_match_historical_baseline() -> None:
    cfg = TranslationConfig(
        target_language="vi",
        mode=TranslationMode.REPLACE,
        tone="neutral",
        domain="general",
    )
    assert build_system_message(cfg) == _baseline_only()


def test_build_system_message_none_tone_domain_same_as_neutral_general() -> None:
    cfg = TranslationConfig(target_language="vi", mode=TranslationMode.REPLACE)
    assert build_system_message(cfg) == _baseline_only()


def test_build_system_message_tone_and_domain_and_instruction() -> None:
    cfg = TranslationConfig(
        target_language="en",
        mode=TranslationMode.BILINGUAL,
        tone="formal",
        domain="legal",
        custom_instruction="Preserve numbered clauses.",
    )
    s = build_system_message(cfg)
    assert _baseline_only() in s
    assert "Subject domain: legal." in s
    assert "Voice and tone: formal." in s
    assert "Additional user instruction:" in s
    assert "Preserve numbered clauses." in s


def test_compose_neighbor_prepends_chunk_rule() -> None:
    cfg = TranslationConfig(
        target_language="vi",
        tone="casual",
        domain="fiction",
        custom_instruction="Keep dialogue snappy.",
    )
    s = compose_neighbor_context_system_instruction(cfg)
    assert "TARGET_CHUNK_START" in s
    assert "Voice and tone: casual." in s
    assert "Subject domain: fiction." in s


def test_normalize_tone_domain_invalid() -> None:
    with pytest.raises(ValueError):
        normalize_tone("invalid")
    with pytest.raises(ValueError):
        normalize_domain("space")


def test_instruction_hash_changes_with_tone() -> None:
    base = TranslationConfig(
        target_language="vi",
        mode=TranslationMode.REPLACE,
        glossary={},
        tone="neutral",
        domain="general",
    )
    lit = TranslationConfig(
        target_language="vi",
        mode=TranslationMode.REPLACE,
        glossary={},
        tone="literary",
        domain="general",
    )
    h0 = hashlib.sha256(build_system_message(base).encode("utf-8")).hexdigest()
    h1 = hashlib.sha256(build_system_message(lit).encode("utf-8")).hexdigest()
    assert h0 != h1
