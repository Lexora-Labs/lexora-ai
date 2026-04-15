# Translation Run Contract

This document freezes the minimal contract between translation core and downstream consumers (CLI, future UI, automation).

## Lifecycle Status

- `dry-run`: validation successful, no translation executed.
- `success`: translation completed and output persisted.
- `failed`: run ended with error.

## CLI Run Report Schema

Top-level fields:

- `command`: command name (`translate`)
- `input_file`
- `output_file`
- `target_language`
- `source_language`
- `mode`
- `cache_scope`
- `dry_run`
- `structured_epub_batch` (boolean)
- `structured_epub_batch_max_chars` (integer)
- `provider` (canonical name)
- `glossary_terms`
- `cache_path`
- `status`
- `elapsed_ms`
- `error` (present on `failed`)
- `token_usage` (present on `success` when available)
- `translation_summary` (present on EPUB runs)

## Translation Summary Fields (EPUB)

- `provider`
- `input_file`
- `output_file`
- `docs_total`
- `docs_translated`
- `nodes_total`
- `chunks_total`
- `cache_hits`
- `cache_misses`
- `cache_hit_rate`
- `cache_entries_before`
- `chunk_size`
- `chunk_context_window`
- `elapsed_ms`
- `structured_batch_enabled` (boolean; true when structured EPUB path is active)
- `structured_batches_total` (integer; provider JSON batch calls that succeeded)
- `structured_items_total` (integer; items sent in those batches)
- `structured_validation_failures` (integer; fallbacks to `translate_batch` after structured failure)
- `structured_fallback_batches` (integer; count of single-item fallbacks)

## Deterministic Guarantees

- Chunk and node order are preserved during reassembly.
- Cache keys remain behavior-aware via fingerprint fields.
- `mode` affects rendering only, not cache key identity.
- Context-window mode must emit target chunk output only.
