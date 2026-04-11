# Translation Logic Notes

This document describes the current canonical translation logic in `lexora-ai`.

## Goal

- Preserve document structure while translating content.
- Keep one canonical provider-based pipeline for CLI, UI, and Python API.
- Stay stateless in the core pipeline.

## Canonical Flow

1. Input file is routed to a reader by file type.
2. Reader extracts content safely with DOM-aware parsing.
3. Translator builds `TranslationConfig` and calls provider (`BaseTranslator`).
4. Provider returns `TranslationResult` (translated content + optional AST data).
5. Output is written in the target format.

## EPUB Logic (Current)

1. Parse EPUB document items (`ITEM_DOCUMENT`) via `ebooklib`.
2. Parse each XHTML document with BeautifulSoup (`lxml-xml`).
3. Collect translatable text nodes only (skip `script`, `style`, `code`, `pre`).
4. Apply sentence-aware safe chunking for long node text.
5. Translate chunks through `provider.translate_batch(...)`.
6. Reassemble translated chunks back to the original node order.
7. Replace DOM text nodes and repack EPUB.

## Why Chunking Exists

- Avoid model failures on very long node text.
- Reduce timeout and token overflow risks.
- Keep translation deterministic by preserving node/chunk order.

## Known Tradeoff

- Chunking improves reliability, but independent chunk calls can reduce cross-chunk context coherence.

## Caching Flow (Planned)

To reduce repeated translation cost and speed up reruns, the pipeline will support a resumable cache.

### Cache model

- Storage format: JSONL (append-only)
- Key strategy: `sha256(target_language + "||" + content)`
- Value: translated output for that exact content in that target language

### Read/write behavior

1. For each node/chunk candidate, compute cache key.
2. Check cache (`get`) before calling provider.
3. If cache hit, use cached translation directly.
4. If cache miss, call provider and persist result (`put`).
5. Reassemble translated chunks back to node order.

### Design rules

- Keep cache lookups deterministic and stateless from pipeline perspective.
- Do not mutate or rewrite existing cache records; append new records only.
- Cache must be optional and configurable (CLI first, then UI).
- Cache must not change output mapping logic: node/chunk ordering stays canonical.

## Planned Improvement (Deferred)

- Add neighbor-window context per chunk so each translation call includes adjacent chunk context while only the target chunk is emitted as output.

## Mode and Glossary

- `mode=replace`: replace original node text.
- `mode=bilingual`: keep original and translated text together.
- `glossary`: term mapping is passed in `TranslationConfig` to providers.
