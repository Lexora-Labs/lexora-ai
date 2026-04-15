"""Structure-preserving JSON batch helpers for EPUB translation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class StructuredBatchItem:
    """One translatable unit in a structured batch request."""

    id: str
    text: str
    type: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None

    def to_request_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"id": self.id, "text": self.text}
        if self.type:
            d["type"] = self.type
        if self.context_before:
            d["context_before"] = self.context_before
        if self.context_after:
            d["context_after"] = self.context_after
        return d


def build_structured_batch_user_payload(
    *,
    source_lang: Optional[str],
    target_lang: str,
    batch_id: str,
    items: List[StructuredBatchItem],
) -> str:
    """Serialize the user message body (JSON string) for the model."""
    payload = {
        "source_lang": source_lang or "auto",
        "target_lang": target_lang,
        "batch_id": batch_id,
        "items": [it.to_request_dict() for it in items],
    }
    return json.dumps(payload, ensure_ascii=False)


def parse_structured_batch_response(raw: str) -> Dict[str, Any]:
    """Parse model output as JSON object."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def validate_and_extract_translations(
    *,
    expected_ids: List[str],
    parsed: Any,
    source_by_id: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Validate response shape and return id -> translated_text.

    Raises ValueError on any contract violation.
    """
    if not isinstance(parsed, dict):
        raise ValueError("structured_batch_response_not_object")

    items = parsed.get("items")
    if not isinstance(items, list):
        raise ValueError("structured_batch_missing_items_array")

    if len(items) != len(expected_ids):
        raise ValueError(
            f"structured_batch_item_count_mismatch expected={len(expected_ids)} got={len(items)}"
        )

    expected_set = set(expected_ids)
    out: Dict[str, str] = {}
    seen: set[str] = set()

    for row in items:
        if not isinstance(row, dict):
            raise ValueError("structured_batch_item_not_object")
        iid = row.get("id")
        if not isinstance(iid, str) or not iid:
            raise ValueError("structured_batch_item_bad_id")
        if iid in seen:
            raise ValueError(f"structured_batch_duplicate_id {iid}")
        seen.add(iid)
        tt = row.get("translated_text")
        if not isinstance(tt, str):
            raise ValueError(f"structured_batch_bad_translated_text id={iid}")

        if iid not in expected_set:
            raise ValueError(f"structured_batch_unexpected_id {iid}")
        out[iid] = tt

    missing = expected_set - seen
    if missing:
        raise ValueError(f"structured_batch_missing_ids {sorted(missing)[:5]}")

    for iid in expected_ids:
        t = out[iid]
        src = (source_by_id or {}).get(iid, "")
        if src.strip() and not t.strip():
            raise ValueError(f"structured_batch_empty_translation id={iid}")

    return out


def pack_items_by_char_budget(
    items: List[StructuredBatchItem],
    max_payload_chars: int,
    overhead_per_batch: int = 400,
) -> List[List[StructuredBatchItem]]:
    """Greedy pack items into batches under an approximate character budget."""
    if max_payload_chars < 500:
        max_payload_chars = 500

    batches: List[List[StructuredBatchItem]] = []
    current: List[StructuredBatchItem] = []
    current_size = overhead_per_batch

    for it in items:
        piece = len(it.text) + len(it.id) + 80
        if current and current_size + piece > max_payload_chars:
            batches.append(current)
            current = []
            current_size = overhead_per_batch
        current.append(it)
        current_size += piece

    if current:
        batches.append(current)

    return batches
