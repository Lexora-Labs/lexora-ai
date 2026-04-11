# Translation Pipeline Planned Todo

Status guide:
- Planned: approved direction, not implemented yet
- In progress: active work
- Done: implemented and verified

| Task ID | Item | Status | Goal | Scope / Notes |
|---|---|---|---|---|
| T-001 | CLI logic to Flet UI | In progress | Keep UI behavior aligned with canonical CLI pipeline | Mirror CLI options (`mode`, `glossary`, chunking behavior) in Flet flow and route through shared `Translator` path |
| T-002 | Implement global cache with robust key fingerprinting | In progress | Reduce translation cost/time while preventing incorrect cross-config cache reuse | Global JSONL cache as primary store; fingerprint includes language pair, provider/model, mode, glossary hash, instruction hash, and pipeline version |
| T-003 | Propose exact cache-key schema and JSONL record format | In progress | Make cache implementation straightforward, safe, and auditable before coding | Define canonical key fields, hashing strategy, metadata fields, and validation rules for read/write behavior |
| T-004 | Add cache scope option (`global`, `per-ebook`, `disabled`) | Planned | Support both reuse efficiency and isolation requirements | CLI-first option with default `global`; UI wiring later |
| T-005 | Add cache migration/versioning strategy | Planned | Keep cache correctness across prompt/chunking/pipeline changes | Introduce `schema_version` and `pipeline_version` in records, with compatibility checks |
| T-006 | Neighbor-window context for chunk translation | Planned (deferred for now) | Improve contextual translation quality across long nodes | For each chunk, include previous and next chunk as context input; output only the target chunk translation |
| T-007 | Configurable chunking controls | Planned | Expose chunk-size controls in CLI and later UI | Add user-facing parameters for chunk size tuning |
| T-008 | Section-level coherence pass | Planned | Optional second pass to harmonize tone and terminology per chapter | Run after first-pass translation for chapter-level consistency |
| T-009 | EPUB golden tests for long-context consistency | Planned | Verify continuity for pronouns, entities, and repeated terms | Add regression fixtures and expected-output checks |
