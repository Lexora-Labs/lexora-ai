# EPUB Structured Batch Translation — Task Plan

This document is the **implementation and sequencing plan** for the design in [epub-structured-batch-translation-design.md](epub-structured-batch-translation-design.md). It is aligned with [todo-list.md](todo-list.md) Task IDs **LAI-T-032** through **LAI-T-035**.

Status: **Shipped** — **LAI-T-032** through **LAI-T-035** are **Done** in [todo-list.md](todo-list.md) after code + doc review (2026-04-15). Live OpenAI/Azure JSON responses remain operator-verified; automated path uses fake provider smoke + unit tests.

## 1. Goals and non-goals

**Goals**

- Reduce EPUB translation **token overhead** and **provider round-trips** using structure-preserving **JSON batch** requests and responses.
- Keep **DOM invariants**, **cache correctness**, and **run report** compatibility per [translation-run-contract.md](translation-run-contract.md).
- Ship first on **OpenAI** and **Azure AI Foundry** GPT-class deployments; other providers unchanged until explicitly extended.

**Non-goals (this iteration)**

- Replacing the entire EPUB path with a single whole-book prompt.
- Changing bilingual rendering semantics (`mode`) beyond wiring through existing post-translation rendering.
- Resolving **LAI-T-006** (neighbor-window chunk context) as a separate feature; structured batches may use optional `context_before` / `context_after` per item without implementing full LAI-T-006.

## 2. References

| Artifact | Role |
|----------|------|
| [epub-structured-batch-translation-design.md](epub-structured-batch-translation-design.md) | JSON contract, validation, batching, cache, observability |
| [translation-logic.md](translation-logic.md) | Current EPUB flow; update after implementation |
| [translation-run-contract.md](translation-run-contract.md) | Report/summary fields; extend per design §10 |
| [testing-epub-samples.md](testing-epub-samples.md) | Primary fixture `samples/accessible_epub_3.epub` |
| [engineering-standards.md](../../lexora-project/docs/20-engineering/engineering-standards.md) | Stateless core, DOM parsing, performance/token budgets |

## 3. Task ID mapping

| Phase | Todo row | Outcome |
|-------|----------|---------|
| Provider layer | **LAI-T-033** (Done) | `translate_structured_batch` on OpenAI + Azure AI Foundry; JSON-only response path |
| Core EPUB pipeline | **LAI-T-032** (Done) | Translation units, char-budget pack, validate, split/fallback to `translate_batch`; cache fingerprint isolation |
| CLI, reports, docs | **LAI-T-034** (Done) | CLI flags, run report + `translation_summary` fields, `translation-logic.md` / contract / README |
| Tests | **LAI-T-035** (Done) | Unit tests for `structured_batch` + cache `epub-structured-json-v1`; EPUB smoke with fake structured provider and `samples/hefty-water.epub` when present (else skip) |

**Related existing todos (not owned by this plan)**

- **LAI-T-009** (EPUB golden tests, long-context): After structured mode is stable, extend golden coverage; coordinate so fixtures do not duplicate effort.
- **LAI-T-018** (structured translation events): Optional alignment when logging batch IDs and validation failures.

## 4. Implementation phases

### Phase A — Provider structured batch (LAI-T-033) — Done

1. Define internal request/response types matching design §4–§5 (provider-agnostic dataclasses or typed dicts in core).
2. **OpenAI**: one call path that sends system/user messages, requires JSON output (schema or instruction per SDK capabilities), returns parsed `items[]`.
3. **Azure AI Foundry**: parallel path reusing the same internal contract; only transport/auth differs.
4. Unit tests with **mocked HTTP** or stubbed client: valid JSON, malformed JSON, truncated output, wrong IDs.

Exit criteria: both providers can return a validated structured response for a synthetic batch in isolation (no EPUB I/O).

### Phase B — Core translator integration (LAI-T-032) — Done

1. After existing **cache resolution** for segments, collect **uncached** items into translation units with stable `id` (document index + sequence or hash-derived stable id — document choice in implementation, must be deterministic per run).
2. **Token-budget packer** (design §6): greedy pack with conservative margin; record `batch_id` for logs.
3. Call provider structured batch; run **strict validator** (design §5).
4. On failure: **repair retry** → **split batch** → **fallback** to current `translate_batch` / merge path for affected items only.
5. **Fingerprint / cache**: extend pipeline/chunking version fingerprint so structured mode never collides with legacy cache entries (per design §9).
6. Manual run: `samples/accessible_epub_3.epub` with structured mode on, `--limit-docs 1`, compare structure to baseline output (no broken spine/links).

Exit criteria: full EPUB translate completes with structured mode enabled; fallback path exercised in tests or fault injection.

### Phase C — CLI, reports, documentation (LAI-T-034) — Done

1. CLI: add opt-in flag(s) for structured JSON batch mode (exact names TBD in implementation PR; default **off** until sign-off).
2. **Run report** and **translation_summary**: add fields from design §10 (`structured_batch_enabled`, batch counts, validation failures, fallbacks).
3. Update **translation-logic.md** with the new branch and interaction with `--merge-max-chars` / `--chunk-context-window` (mutually exclusive rules if any).
4. Update **README** / **providers.md** if operator-facing behavior changes.

Exit criteria: `--report-path` JSON documents new fields when structured mode is used; docs match code.

### Phase D — Tests and hardening (LAI-T-035) — Done

1. **Unit**: validator, batch pack, and cache fingerprint covered in `test_basic.py`.
2. **Integration**: EPUB smoke with fake structured provider (`samples/hefty-water.epub` when present; otherwise explicit skip).
3. **Manual**: operators may still run `samples/accessible_epub_3.epub` with structured flags per **testing-epub-samples.md**.

Exit criteria: `test_basic.py` green; plan checklist updated to match shipped tests.

## 5. Acceptance checklist

- [x] Structured mode off by default; legacy path unchanged (`structured_epub_batch` default false; CLI `store_true`).
- [x] OpenAI + Azure AI Foundry implement `translate_structured_batch` (live calls verified by operators; CI uses fake provider smoke).
- [x] Invalid model output: provider repair attempt + translator split / per-item `translate_batch` fallback; non-retryable errors do not amplify splits.
- [x] Cache keys: `epub-structured-json-v1` vs `epub-node-v1` pipeline + chunking fingerprint separation in `translation_cache.py`.
- [x] LAI-T-035: automated coverage in `test_basic.py` (no API keys); full `accessible_epub_3.epub` structured translate remains a recommended manual check per [testing-epub-samples.md](testing-epub-samples.md).
- [x] Run report and `translation_summary` include structured-batch metrics when enabled ([translation-run-contract.md](translation-run-contract.md), `cli.py` report payload).

## 6. Risk register (execution)

| Risk | Mitigation |
|------|------------|
| JSON schema drift across providers | Single internal schema; adapter normalizes |
| Large batches harm latency | Token cap + concurrency limits consistent with provider quotas |
| Inline-heavy HTML degrades | Hybrid smaller units (design §12); tune after first metrics |

## 7. Branch and governance

- Implementation work should land on a dedicated improvement branch (for example `improvement/epub-structured-batch-translation`) and reference these Task IDs in commits/PRs.
- If process or cross-repo milestones change, sync **lexora-project** planning per [documentation-governance.md](../../lexora-project/docs/30-governance/documentation-governance.md).
