# UI data model (Flet)

This document tracks **structured state and types** the Flet UI owns or coordinates. It is for contributors: what exists today, where it lives, and how it relates to the core translation contract.

For the **CLI / disk run report** and EPUB summary fields from the engine, see [`translation-run-contract.md`](translation-run-contract.md).

---

## 1. Translation job record (`TranslationJob` + `JobStore`)

**Location:** `src/lexora/ui/job_store.py`

This is the only **shared, first-class domain object** wired across Translate and Jobs today: a single in-memory store (`JobStore`) holds `TranslationJob` rows for the current app session (not persisted to disk).

### `TranslationJob` fields

| Field | Meaning |
| ----- | ------- |
| `id` | Canonical identifier for the run (**JobId = RunId**). Format: `run-{uuid_hex}`. |
| `run_id` | Property; same value as `id`. |
| `book_title` | Display/job name (typically the input file display name or basename). |
| `provider` | UI provider label (e.g. `OpenAI`). |
| `model` | Model name string. |
| `target_lang` | Target language code. |
| `status` | `queued` \| `in_progress` \| `completed` \| `failed` \| `cancelled`. |
| `progress` | `0.0`–`1.0` for UI progress bar. |
| `created_at` | Wall-clock string when the job row was created (`YYYY-MM-DD HH:MM:SS`, local). |
| `parameters` | Deep copy of the UI **run request** dict (see §2). |
| `started_at` | Set when the worker thread actually begins the run (`mark_run_started`). Empty while only queued. |
| `completed_at` | Set when status becomes terminal (`completed` / `failed` / `cancelled`). |
| `duration_ms` | Wall duration for terminal runs that executed in the worker (may be unset for queue-only cancellations). |
| `total_docs` | EPUB: count of spine documents selected for the run (preflight); refined on success from engine metadata when available. Non-EPUB: `1`. |
| `docs_translated` | From engine EPUB metadata on success when available; may be `0` at preflight. |
| `error` | Failure message when `status == failed`. |
| `output_path` | Resolved output file path once known (desktop: open file / reveal folder). |
| `log_cursor_start` / `log_cursor_end` | Indices into the in-memory UI log ring buffer (`get_ui_log_events`) bounding lines captured for this job. |

### `JobStore` operations (summary)

- `create_job`, `get_job`, `delete_job` (blocks delete while `in_progress`)
- `mark_run_started`, `update_doc_counts`, `set_doc_progress` (in-run progress uses denominator ``docs_total + 2`` for extract/repack; numerator ``1 + min(docs_completed, docs_total)`` until terminal ``set_status`` sets 100%)
- `set_output_path`, `set_log_cursor_start`, `set_log_cursor_end`
- `set_status` (optional `duration_ms`, `total_docs`, `docs_translated` on terminal states)
- `subscribe` / `snapshot` for UI refresh

Translation runs can be cooperatively cancelled: ``Translator.translate_file(..., cancel_requested=...)`` raises ``TranslationCancelled`` between EPUB spine items and before repack / plain-text write; the Translate screen wires this to the user cancel control.

---

## 2. UI run request (`parameters` on `TranslationJob`)

**Authoritative builder:** `TranslateScreen._build_run_request()` in `src/lexora/ui/screens/translate.py`

The job’s `parameters` dict is a snapshot of that return value (same keys). Typical keys:

- `input_file`, `book_title`
- `provider_label`, `model_name`, `target_lang`, `source_language`
- `mode`, `glossary_path`, `output_override`, `report_path`
- `limit_docs`, `start_doc`, `end_doc`
- `chunk_size`, `chunk_context_window`
- `structured_epub_batch`, `structured_epub_batch_max_chars`

**Note:** Cache scope/path and flags used at execution time are merged from Settings / client storage inside the worker; they are logged and passed to the translator but are not necessarily duplicated inside this dict unless the implementation is extended.

---

## 3. Translate screen coordination (not a persisted model)

**Location:** `src/lexora/ui/screens/translate.py`

These are **internal** structures, not exported datatypes:

| Name | Role |
| ---- | ---- |
| `_queued_jobs` | `deque` of `(store_job_id, request_dict)` for FIFO queue when a run is already active. |
| `_job_requests` | `dict[store_job_id, request_dict]` retained for cancel/retry and parity with `TranslationJob.parameters`. |
| `_active_store_job_id` | Which `TranslationJob.id` is currently bound to the visible Translate controls. |
| `_active_job_id` / `_cancel_requested` | Concurrency and cooperative cancel flags for the worker thread. |

Document count preflight for EPUB uses local helpers that mirror translator document selection (`_apply_epub_doc_selection`, `_count_documents_for_run` in the same module).

---

## 4. Library screen `Book` (mock-only today)

**Location:** `src/lexora/ui/screens/library.py`

- **`Book`** (`@dataclass`): `id`, `title`, `author`, `source_lang`, `target_lang`, `pages`, `translated_at`, `file_path`, `status`.
- **`MOCK_BOOKS`**: in-memory sample list; not connected to `JobStore` or disk library yet.

See task **LAI-T-041** (deferred) for replacing this with a real library model.

---

## 5. Theme tokens (`Colors`)

**Location:** `src/lexora/ui/theme.py`

- **`Colors`**: frozen `@dataclass` of hex strings for surfaces, text, primary, semantic colors, etc. Styling contract for screens, not a translation-domain object.

---

## Summary: “only Job?”

For **cross-screen translation lifecycle and monitoring**, yes: the shared object is **`TranslationJob` inside `JobStore`**.

Other recent or adjacent UI types:

| Type | Shared? | Purpose |
| ---- | -------- | ------- |
| `TranslationJob` | Yes (Translate + Jobs) | One translation run row. |
| Run request `dict` | Duplicated in `_job_requests` + `TranslationJob.parameters` | Input snapshot for retry/details. |
| `Book` | Library screen only | Mock catalog row until Library rework. |
| `Colors` | All screens | Visual tokens. |

When adding persistence (disk or API), treat **`TranslationJob`** (+ optional normalization of `parameters`) as the primary schema candidate; keep alignment with [`translation-run-contract.md`](translation-run-contract.md) for fields that overlap run reports and EPUB summaries.
