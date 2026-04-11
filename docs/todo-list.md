# Translation Pipeline Planned Todo

Status guide:
- Planned: approved direction, not implemented yet
- In progress: active work
- Ready for review: implementation completed locally, pending maintainer verification
- Done: implemented and verified

Metadata guide:
- Datetime format: `YYYY-MM-DDTHH:mm:ss±HH:mm`
- `Created`: set once when task is created
- `Updated`: refresh whenever status, scope, goal, or notes change

Example:
- Created: `2026-04-11T22:08:25+07:00`
- Updated: `2026-04-12T09:15:00+07:00`

| Task ID | Item | Status | Type | Goal | Scope / Notes | Created | Updated |
|---|---|---|---|---|---|---|---|
| LAI-T-001 | CLI logic to Flet UI | In progress | Task | Keep UI behavior aligned with canonical CLI pipeline | Mirror CLI options (`mode`, `glossary`, chunking behavior) in Flet flow and route through shared `Translator` path | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-002 | Implement global cache with robust key fingerprinting | Done | Task | Reduce translation cost/time while preventing incorrect cross-config cache reuse | Implemented global JSONL cache in core translation flow with behavior-aware fingerprint fields | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:56:09+07:00 |
| LAI-T-003 | Propose exact cache-key schema and JSONL record format | Done | Task | Make cache implementation straightforward, safe, and auditable before coding | Implemented `translation_cache.py` schema (`schema_version`, `key`, `content_hash`, `translated_text`, `fingerprint`, `created_at`) and deterministic key strategy | 2026-04-11T22:08:25+07:00 | 2026-04-11T23:01:42+07:00 |
| LAI-T-004 | Add cache scope option (`global`, `per-ebook`, `disabled`) | Planned | Task | Support both reuse efficiency and isolation requirements | CLI-first option with default `global`; UI wiring later | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-005 | Add cache migration/versioning strategy | Planned | Task | Keep cache correctness across prompt/chunking/pipeline changes | Introduce `schema_version` and `pipeline_version` in records, with compatibility checks | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-012 | Add cache clear option for CLI runs | Planned | Task | Allow safe reset of translation cache when users need fresh reruns | Add `--clear-cache` flow to remove current cache file before translation starts; print explicit confirmation and no-op message when file does not exist | 2026-04-11T22:53:52+07:00 | 2026-04-11T22:53:52+07:00 |
| LAI-T-006 | Neighbor-window context for chunk translation | Planned (deferred for now) | Task | Improve contextual translation quality across long nodes | For each chunk, include previous and next chunk as context input; output only the target chunk translation | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-007 | Configurable chunking controls | Planned | Task | Expose chunk-size controls in CLI and later UI | Add user-facing parameters for chunk size tuning | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-010 | Add CLI progress logging for long EPUB runs | Done | Task | Improve test visibility and operator confidence during long translations | Added structured console logs for document count, per-document progress, provider chunk translation calls, cache hit/miss summary, and final completion timing | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:34:13+07:00 |
| LAI-T-011 | Add scoped EPUB test-run parameters (`--limit-docs`, page/chapter range) | Done | Task | Reduce end-to-end test time on large books | Added CLI options `--limit-docs`, `--start-doc`, `--end-doc` with validation and EPUB doc-selection logic in translator | 2026-04-11T22:08:25+07:00 | 2026-04-11T23:04:19+07:00 |
| LAI-B-001 | EPUB output displays raw HTML content | Planned | Bug | Restore correct EPUB reader output rendering after translation | Repro: CLI EPUB translate run; Actual: translated content appears as raw HTML; Expected: valid readable EPUB content; Suspected area: DOM text-node replacement/repack path in translator EPUB pipeline | 2026-04-11T22:22:42+07:00 | 2026-04-11T22:22:42+07:00 |
| LAI-T-008 | Section-level coherence pass | Planned | Task | Optional second pass to harmonize tone and terminology per chapter | Run after first-pass translation for chapter-level consistency | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-009 | EPUB golden tests for long-context consistency | Planned | Task | Verify continuity for pronouns, entities, and repeated terms | Add regression fixtures and expected-output checks | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
