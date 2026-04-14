"""EPUB translation: merge multiple text chunks into one provider call with stable segment markers."""

from __future__ import annotations

import re
from typing import List, Tuple

# Rare bracket markers; unlikely in prose. Same id in open/close for pairing.
_MARK_OPEN = "⟦LX:{:06d}⟧"
_MARK_CLOSE = "⟦/LX:{:06d}⟧"

# Lenient: optional whitespace inside markers, 1–6 digit ids (normalized to int).
_LOOSE_PAIR_RE = re.compile(
    r"⟦\s*LX\s*:\s*(\d{1,6})\s*⟧\s*(.*?)\s*⟦\s*/\s*LX\s*:\s*\1\s*⟧",
    re.DOTALL | re.IGNORECASE,
)


def segment_open(idx: int) -> str:
    return _MARK_OPEN.format(idx)


def segment_close(idx: int) -> str:
    return _MARK_CLOSE.format(idx)


def build_segmented_payload(segments: List[str]) -> str:
    """Wrap each segment with numbered markers (0 .. n-1)."""
    parts: List[str] = []
    for i, text in enumerate(segments):
        parts.append(segment_open(i))
        parts.append("\n")
        parts.append(text)
        parts.append("\n")
        parts.append(segment_close(i))
        parts.append("\n")
    return "".join(parts).rstrip() + "\n"


def _parse_strict(response: str, n: int) -> List[str]:
    pos = 0
    out: List[str] = []
    for i in range(n):
        o = segment_open(i)
        c = segment_close(i)
        start = response.find(o, pos)
        if start < 0:
            raise ValueError(f"missing open marker for segment {i}")
        body_start = start + len(o)
        end = response.find(c, body_start)
        if end < 0:
            raise ValueError(f"missing close marker for segment {i}")
        out.append(response[body_start:end].strip())
        pos = end + len(c)
    return out


def _parse_loose(response: str, n: int) -> List[str]:
    """Recover when model adds spaces inside markers."""
    found: dict[int, str] = {}
    for m in _LOOSE_PAIR_RE.finditer(response):
        idx = int(m.group(1))
        if 0 <= idx < n:
            found[idx] = m.group(2).strip()
    if len(found) != n or set(found.keys()) != set(range(n)):
        raise ValueError(f"loose parse got {len(found)} valid segments, need {n}")
    return [found[i] for i in range(n)]


def parse_segmented_response(response: str, expected_count: int) -> List[str]:
    """
    Extract translated segments in order. Tries strict marker match first, then lenient regex.
    """
    if expected_count == 0:
        return []
    if expected_count == 1:
        text = (response or "").strip()
        o0, c0 = segment_open(0), segment_close(0)
        if o0 in text and c0 in text:
            start = text.index(o0) + len(o0)
            end = text.index(c0, start)
            return [text[start:end].strip()]
        return [text]

    try:
        return _parse_strict(response, expected_count)
    except ValueError:
        return _parse_loose(response, expected_count)


def partition_for_merge(
    uncached_indices: List[int],
    uncached_texts: List[str],
    merge_max_chars: int,
    marker_overhead: int = 32,
) -> List[List[Tuple[int, str]]]:
    """
    Group uncached (chunk_index, text) into batches under merge_max_chars
    (including estimated per-segment marker overhead).
    """
    if len(uncached_indices) != len(uncached_texts):
        raise ValueError("uncached_indices and uncached_texts length mismatch")

    batches: List[List[Tuple[int, str]]] = []
    current: List[Tuple[int, str]] = []
    current_size = 0

    for chunk_idx, txt in zip(uncached_indices, uncached_texts):
        cost = len(txt) + marker_overhead
        if current and current_size + cost > merge_max_chars:
            batches.append(current)
            current = []
            current_size = 0
        current.append((chunk_idx, txt))
        current_size += cost

    if current:
        batches.append(current)

    return batches


MERGE_BATCH_SYSTEM_SUFFIX = (
    "The user message contains {n} segments. Each segment begins with a line ⟦LX:NNNNNN⟧ "
    "and ends with ⟦/LX:NNNNNN⟧ (same six-digit number). "
    "Translate ONLY the human-readable text between each opening and closing marker. "
    "Copy every marker line exactly (same digits and brackets). "
    "Do not merge, omit, reorder, or renumber segments. "
    "Do not wrap the whole reply in markdown fences. "
    "Output must include all {n} segment pairs."
)
