# Translation Logic Notes

This document describes the current canonical translation logic in `lexora-ai`.

## Goal

- Preserve document structure while translating content.
- Keep one canonical provider-based pipeline for CLI, UI, and Python API.
- Stay stateless in the core pipeline.

## Canonical Runtime Entry

- Supported CLI/runtime path: `lexora translate ...` -> `src/lexora/cli.py` -> `Translator`.
- Legacy script path `translate.py` is deprecated and intentionally redirects to the canonical CLI command.

## Canonical Flow

1. Input file is routed to a reader by file type.
2. Reader extracts content safely with DOM-aware parsing.
3. Translator builds `TranslationConfig` and calls provider (`BaseTranslator`).
4. Provider returns `TranslationResult` (translated content + optional AST data).
5. Output is written in the target format.

## EPUB Logic (Current)

1. Parse EPUB document items (`ITEM_DOCUMENT`) via `ebooklib`.
2. Parse each XHTML document with BeautifulSoup (`lxml-xml`).
3. Collect translatable text nodes only (skip `script`, `style`, `code`, `pre`, and any string whose parent is the BeautifulSoup document root — `lxml-xml` can otherwise expose a spurious `"html"` text node that corrupts XHTML if replaced).
4. Apply sentence-aware safe chunking for long node text.
5. Translate **uncached** chunks:
  - **Default:** `provider.translate_batch(...)` per chunk (or batched lists as implemented by the provider).
  - **Optional (`--structured-epub-batch`):** pack multiple chunks into one JSON request/response via `provider.translate_structured_batch(...)` when the provider reports `supports_structured_batch()` (OpenAI, Azure AI Foundry, Gemini). Incompatible with `--chunk-context-window` > 0. On parse/validation failure, the pipeline splits batches and falls back to `translate_batch` for failing items.
6. Reassemble translated chunks back to the original node order.
7. Replace DOM text nodes and repack EPUB.

Structured EPUB mode uses fingerprint `pipeline_version=epub-structured-json-v1` and `chunking_version=sentence-aware-structured-v1` so cache entries do not collide with the default EPUB path.

## Why Chunking Exists

- Avoid model failures on very long node text.
- Reduce timeout and token overflow risks.
- Keep translation deterministic by preserving node/chunk order.

## Known Tradeoff

- Chunking improves reliability, but independent chunk calls can reduce cross-chunk context coherence.

## Caching Flow (Current)

To reduce repeated translation cost and speed up reruns, the pipeline uses a resumable global cache.

### Cache model

- Storage format: JSONL (append-only)
- Key strategy: deterministic hash of content + behavior fingerprint
- Fingerprint fields: source language, target language, provider name, provider model, glossary hash, custom instruction hash, chunking version, pipeline version
- Value: translated output for that exact content under that translation behavior
- Schema fields: `schema_version`, `created_at`, `key`, `content_hash`, `translated_text`, `fingerprint`

### Read/write behavior

1. For each node/chunk candidate, compute cache key.
2. Check cache (`get`) before calling provider.
3. If cache hit, use cached translation directly.
4. If cache miss, call provider and persist result (`put`).
5. Reassemble translated chunks back to node order.
6. Apply output rendering mode (`replace` or `bilingual`) after translation reuse.

### Design rules

- Keep cache lookups deterministic and stateless from pipeline perspective.
- Do not mutate or rewrite existing cache records; append new records only.
- Cache must be optional and configurable (CLI first, then UI).
- Cache must not change output mapping logic: node/chunk ordering stays canonical.

## Planned Improvement (Deferred)

- Add neighbor-window context per chunk so each translation call includes adjacent chunk context while only the target chunk is emitted as output.

## CLI Production Controls (Current)

- `--require-service`: fail unless provider is explicitly selected.
- `--dry-run`: validate input/provider/args without running translation.
- `--report-path`: write machine-readable JSON run report.
- `--chunk-size`: control sentence-aware chunk sizing.
- `--chunk-context-window`: include neighbor chunks as context (target-only output).
- `--structured-epub-batch`: EPUB only; JSON multi-item structured batches (supported providers only).
- `--structured-epub-batch-max-chars`: approximate max source characters per structured batch (default 8000, minimum 2000).

## Runtime Contract

- Canonical run/report contract is defined in `docs/translation-run-contract.md`.

## Mode and Glossary

- `mode=replace`: replace original node text.
- `mode=bilingual`: keep original and translated text together.
- `mode` is a rendering concern and does not change cache identity.
- `glossary`: term mapping is passed in `TranslationConfig` to providers.