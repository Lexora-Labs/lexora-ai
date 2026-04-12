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
| LAI-T-004 | Add cache scope option (`global`, `per-ebook`, `disabled`) | Done | Task | Support both reuse efficiency and isolation requirements | Implemented CLI `--cache-scope` with `global`, `per-ebook`, and `disabled`; per-ebook scope derives deterministic cache path from input file identity | 2026-04-11T22:08:25+07:00 | 2026-04-12T12:27:38+07:00 |
| LAI-T-005 | Add cache migration/versioning strategy | Done | Task | Keep cache correctness across prompt/chunking/pipeline changes | Added compatibility filtering on cache load: accept only supported `schema_version` and `fingerprint.pipeline_version`; persist top-level `pipeline_version` for easier audits | 2026-04-11T22:08:25+07:00 | 2026-04-12T12:27:38+07:00 |
| LAI-T-012 | Add cache clear option for CLI runs | Done | Task | Allow safe reset of translation cache when users need fresh reruns | Implemented `--clear-cache` against effective scope path (`global`/`per-ebook`) with explicit cleared/no-op/disabled messages before run start | 2026-04-11T22:53:52+07:00 | 2026-04-12T12:27:38+07:00 |
| LAI-T-013 | Define centralized logging framework spec | Planned | Task | Establish one shared logging architecture before implementation | Document sink model (console/file/Azure/AWS), config contract, structured event fields, and rollout constraints in `docs/logging-framework.md` | 2026-04-12T12:16:11+07:00 | 2026-04-12T12:16:11+07:00 |
| LAI-T-014 | Implement logger bootstrap and sink routing | Planned | Task | Replace ad-hoc prints with configurable logger routing | Add shared logger bootstrap module, parse targets and level from env/CLI, and support multi-sink activation with safe fallback to console | 2026-04-12T12:16:11+07:00 | 2026-04-12T12:16:11+07:00 |
| LAI-T-015 | Add rotating file sink and retention controls | Planned | Task | Provide persistent local logs for long EPUB runs and troubleshooting | Add rotating file handler with path/max-bytes/backup-count config and verify UTF-8 log output | 2026-04-12T12:16:11+07:00 | 2026-04-12T12:16:11+07:00 |
| LAI-T-016 | Add Azure Monitor log export sink | Planned | Task | Enable optional Azure-side observability without changing core behavior | Add optional Azure sink integration via connection string; on missing dependency/config, emit warning and continue local sinks | 2026-04-12T12:16:11+07:00 | 2026-04-12T12:16:11+07:00 |
| LAI-T-017 | Add AWS CloudWatch log export sink | Planned | Task | Enable optional AWS-side observability for hybrid deployments | Add optional CloudWatch sink integration with log-group/stream/region config; keep graceful fallback on errors | 2026-04-12T12:16:11+07:00 | 2026-04-12T12:16:11+07:00 |
| LAI-T-018 | Add structured translation event schema | Planned | Task | Standardize log fields for filtering, supportability, and future analytics | Define event keys (`run_id`, `provider`, `doc_index`, `chunks`, `cache_hit/miss`, `elapsed_ms`) and map core/provider events consistently | 2026-04-12T12:16:11+07:00 | 2026-04-12T12:16:11+07:00 |
| LAI-T-019 | Render shared logs in Flet UI | Planned | Task | Surface real-time operational logs in desktop app without duplicate pipelines | Add UI log panel that consumes shared logger events, supports level filter and incremental updates, and preserves non-blocking UI behavior | 2026-04-12T12:16:11+07:00 | 2026-04-12T12:16:11+07:00 |
| LAI-T-006 | Neighbor-window context for chunk translation | Planned (deferred for now) | Task | Improve contextual translation quality across long nodes | For each chunk, include previous and next chunk as context input; output only the target chunk translation | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-007 | Configurable chunking controls | Planned | Task | Expose chunk-size controls in CLI and later UI | Add user-facing parameters for chunk size tuning | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-010 | Add CLI progress logging for long EPUB runs | Done | Task | Improve test visibility and operator confidence during long translations | Added structured console logs for document count, per-document progress, provider chunk translation calls, cache hit/miss summary, and final completion timing | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:34:13+07:00 |
| LAI-T-011 | Add scoped EPUB test-run parameters (`--limit-docs`, page/chapter range) | Done | Task | Reduce end-to-end test time on large books | Added CLI options `--limit-docs`, `--start-doc`, `--end-doc` with validation and EPUB doc-selection logic in translator | 2026-04-11T22:08:25+07:00 | 2026-04-11T23:04:19+07:00 |
| LAI-B-001 | EPUB output displays raw HTML content | Planned | Bug | Restore correct EPUB reader output rendering after translation | Repro: CLI EPUB translate run; Actual: translated content appears as raw HTML; Expected: valid readable EPUB content; Suspected area: DOM text-node replacement/repack path in translator EPUB pipeline | 2026-04-11T22:22:42+07:00 | 2026-04-11T22:22:42+07:00 |
| LAI-T-008 | Section-level coherence pass | Planned | Task | Optional second pass to harmonize tone and terminology per chapter | Run after first-pass translation for chapter-level consistency | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
| LAI-T-009 | EPUB golden tests for long-context consistency | Planned | Task | Verify continuity for pronouns, entities, and repeated terms | Add regression fixtures and expected-output checks | 2026-04-11T22:08:25+07:00 | 2026-04-11T22:08:25+07:00 |
