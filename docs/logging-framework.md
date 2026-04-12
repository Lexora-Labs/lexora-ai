# Logging Framework Plan

This document defines the planned logging framework for `lexora-ai` before implementation.

## Goals

- Provide one centralized logging framework for all runtime paths.
- Support multi-sink logging: console, file, Azure Monitor, and AWS CloudWatch.
- Keep core pipeline behavior unchanged while improving observability.
- Keep default setup lightweight and safe for local development.
- Support rendering operational logs in Flet UI without introducing a second backend path.

## Scope

Applies to:

- CLI execution
- Core translation pipeline (`Translator`, readers, providers, cache flow)
- UI runtime (Flet) as a log consumer/renderer

Does not include:

- Metrics/tracing implementation details (future extension)
- Centralized log storage provisioning in cloud infrastructure

## Design Principles

- Single source of truth: one logger bootstrap/config module.
- Stateless core: no request/session state stored globally in pipeline logic.
- Structured logs: predictable event fields for filtering and diagnostics.
- Optional cloud sinks: Azure/AWS integrations are opt-in and non-blocking.
- Graceful fallback: if cloud sink setup fails, continue with local sinks.

## Sink Model

Supported sinks:

1. `console`
2. `file` (rotating)
3. `azure` (Azure Monitor / Application Insights export)
4. `aws` (CloudWatch export)
5. `ui` (in-app sink for desktop log rendering)

Target selection model:

- Comma-separated list from config, for example: `console,file` or `console,azure`.
- Multiple sinks can be enabled at once.
- UI sink can be combined with other sinks, for example: `console,file,ui`.

## Generic Logging Structure (Winston Mapping)

The framework follows the same generic structure used by Winston-style systems:

1. Logger
2. Levels
3. Formatter
4. Transports (sinks)
5. Per-transport configuration
6. Context fields

Winston-to-Lexora mapping:

| Winston concept | Lexora plan |
|---|---|
| `createLogger(...)` | Centralized logger bootstrap module |
| `level` | `LEXORA_LOG_LEVEL` |
| `format.combine(...)` | Shared formatter + structured event contract |
| `transports.Console` | `console` sink |
| `transports.File` | `file` sink with rotation |
| Cloud transports/plugins | `azure` and `aws` sinks |
| Custom transport | `ui` sink for desktop rendering |

## Configuration Model

Planned configuration keys (env and CLI override ready):

- `LEXORA_LOG_LEVEL` (default: `INFO`)
- `LEXORA_LOG_TARGETS` (default: `console`)
- `LEXORA_LOG_FILE_PATH` (default: `logs/lexora.log`)
- `LEXORA_LOG_FILE_MAX_BYTES` (default: `5242880`)
- `LEXORA_LOG_FILE_BACKUP_COUNT` (default: `3`)
- `LEXORA_AZURE_MONITOR_CONNECTION_STRING`
- `LEXORA_AWS_LOG_GROUP`
- `LEXORA_AWS_LOG_STREAM`
- `LEXORA_AWS_REGION`
- `LEXORA_LOG_UI_BUFFER_SIZE` (default: `500`)
- `LEXORA_LOG_UI_MIN_LEVEL` (default: `INFO`)

## Log File Naming Pattern (Winston-Inspired)

Follow a Winston-style date token convention for file sinks.

Pattern baseline:

- `lexora-%DATE%.log`

Date token format:

- `%DATE%` -> `YYYY-MM-DD`

Recommended variants:

1. Combined app log:
	- `lexora-%DATE%.log`
2. Error-only log:
	- `lexora-error-%DATE%.log`
3. Optional provider-segmented log:
	- `lexora-{provider}-%DATE%.log`

Examples:

- `lexora-2026-04-12.log`
- `lexora-error-2026-04-12.log`
- `lexora-azure-foundry-2026-04-12.log`

Windows-safe rule:

- Do not include `:` in file names; use date-only token (`YYYY-MM-DD`) for portability.

Rotation behavior:

- Date-based file naming plus size-based rotation is allowed.
- If size rotation occurs within the same day, append numeric suffixes:
  - `lexora-2026-04-12.log.1`, `lexora-2026-04-12.log.2`

## Structured Event Contract

Common fields expected on operational events:

- `event`
- `run_id`
- `provider`
- `source_language`
- `target_language`
- `input_file`
- `output_file`
- `doc_index`
- `doc_total`
- `chunks`
- `cache_hit`
- `cache_miss`
- `elapsed_ms`

## Flet UI Rendering Support

The framework must support UI rendering by exposing a UI-safe log feed model:

- UI receives formatted or structured log events from the shared logger path.
- UI sink target name is `ui` and must subscribe to the same event contract as other sinks.
- UI does not define separate translation logs; it renders the same events emitted by CLI/core.
- UI-level filters can scope by level, stage, or run id.
- UI buffer should be bounded and drop oldest entries first to avoid memory pressure.
- Long-running translation should stream logs incrementally to avoid frozen status displays.

## Rollout Plan

1. Add logger bootstrap module and config contract.
2. Replace `print(...)` in CLI and `Translator` with logger calls.
3. Migrate provider debug prints to logger debug/warn/error levels.
4. Add file sink support and rotation defaults.
5. Add Azure sink (optional dependency).
6. Add AWS sink (optional dependency).
7. Add Flet UI log rendering adapter to consume shared events.
8. Add tests and documentation examples.

## Validation Criteria

- Default local run logs to console with no extra setup.
- File sink writes and rotates correctly.
- Azure/AWS sink misconfiguration does not break translation.
- CLI and UI show consistent event semantics for the same run.
- Flet UI can render progress and errors from shared logging events.
