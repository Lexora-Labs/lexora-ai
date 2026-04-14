"""Tests for EPUB merged-segment batching helpers."""

import pytest

from lexora.epub_segment_batch import (
    build_segmented_payload,
    parse_segmented_response,
    partition_for_merge,
)


def test_build_parse_roundtrip_strict():
    segments = ["Alpha", "Beta line", "Gamma"]
    payload = build_segmented_payload(segments)
    out = parse_segmented_response(payload, 3)
    assert out == ["Alpha", "Beta line", "Gamma"]


def test_parse_loose_whitespace_in_markers():
    segments = ["One", "Two"]
    payload = build_segmented_payload(segments)
    # Simulate model adding spaces inside markers
    messy = payload.replace("⟦LX:", "⟦ LX : ").replace("⟧", " ⟧")
    out = parse_segmented_response(messy, 2)
    assert out == ["One", "Two"]


def test_partition_for_merge_respects_budget():
    texts = ["a" * 100, "b" * 100, "c" * 100]
    idx = [0, 1, 2]
    batches = partition_for_merge(idx, texts, merge_max_chars=250, marker_overhead=40)
    assert len(batches) >= 2
    total_items = sum(len(b) for b in batches)
    assert total_items == 3


def test_single_segment_no_markers():
    assert parse_segmented_response("  plain  ", 1) == ["plain"]
