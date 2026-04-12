"""Translation cache helpers for deterministic, fingerprinted reuse."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


CACHE_SCHEMA_VERSION = "1.0"
SUPPORTED_CACHE_SCHEMA_VERSIONS = {"1.0"}
SUPPORTED_PIPELINE_VERSIONS = {"epub-node-v1"}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_json(data: Dict[str, str]) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def hash_glossary(glossary: Dict[str, str]) -> str:
    """Return stable glossary hash for cache fingerprinting."""
    normalized = {str(k): str(v) for k, v in (glossary or {}).items()}
    return _sha256(_stable_json(normalized))


@dataclass(frozen=True)
class CacheFingerprint:
    """Cache fingerprint fields that define translation behavior."""

    source_language: str
    target_language: str
    provider_name: str
    provider_model: str
    glossary_hash: str
    instruction_hash: str
    chunking_version: str
    pipeline_version: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "source_language": self.source_language,
            "target_language": self.target_language,
            "provider_name": self.provider_name,
            "provider_model": self.provider_model,
            "glossary_hash": self.glossary_hash,
            "instruction_hash": self.instruction_hash,
            "chunking_version": self.chunking_version,
            "pipeline_version": self.pipeline_version,
        }


def build_cache_key(content: str, fingerprint: CacheFingerprint) -> str:
    """Build a stable cache key using content hash + behavior fingerprint hash."""
    content_hash = _sha256(content)
    fingerprint_hash = _sha256(_stable_json(fingerprint.to_dict()))
    return _sha256(f"{content_hash}||{fingerprint_hash}")


class TranslationCache:
    """Append-only JSONL cache with in-memory lookup map."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._map: Dict[str, str] = {}
        self._supported_schema_versions = SUPPORTED_CACHE_SCHEMA_VERSIONS
        self._supported_pipeline_versions = SUPPORTED_PIPELINE_VERSIONS
        self._load_existing()

    def _load_existing(self) -> None:
        if not self.path.exists():
            return

        with open(self.path, "r", encoding="utf-8") as cache_file:
            for line in cache_file:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                schema_version = str(record.get("schema_version", ""))
                if schema_version not in self._supported_schema_versions:
                    continue

                fingerprint = record.get("fingerprint")
                if not isinstance(fingerprint, dict):
                    continue

                pipeline_version = str(fingerprint.get("pipeline_version", ""))
                if pipeline_version not in self._supported_pipeline_versions:
                    continue

                key = record.get("key")
                translated_text = record.get("translated_text")
                if isinstance(key, str) and isinstance(translated_text, str):
                    self._map[key] = translated_text

    def get(self, content: str, fingerprint: CacheFingerprint) -> Optional[str]:
        key = build_cache_key(content, fingerprint)
        return self._map.get(key)

    def put(self, content: str, fingerprint: CacheFingerprint, translated_text: str) -> None:
        key = build_cache_key(content, fingerprint)
        if key in self._map:
            return

        record = {
            "schema_version": CACHE_SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "key": key,
            "content_hash": _sha256(content),
            "translated_text": translated_text,
            "fingerprint": fingerprint.to_dict(),
            "pipeline_version": fingerprint.pipeline_version,
        }

        with open(self.path, "a", encoding="utf-8") as cache_file:
            cache_file.write(json.dumps(record, ensure_ascii=False) + "\n")

        self._map[key] = translated_text
