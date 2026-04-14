# Track A MVP Plan (2 Weeks): Translation Core + CLI

## Scope
- Prioritize translation core reliability and CLI-first production controls.
- Defer broader Flet UI feature expansion until core contracts are stable.

## MVP Outcomes
- One canonical translation runtime path.
- CLI preflight safety and explicit provider control.
- Machine-readable run report output for CI/ops.
- Stable translation contract for future UI integration.

## Week 1
- Canonicalize runtime path around `Translator` + provider factory.
- Add CLI production guardrails:
  - `--require-service` (fail if provider is not explicit)
  - `--dry-run` (validate config/provider/input without executing translation)
  - `--report-path` (write run metadata JSON)
- Normalize provider naming in CLI/report output to canonical names.

## Week 2
- Add translation quality controls:
  - context-window chunk translation strategy (target chunk output only)
  - configurable chunk size controls via CLI
- Standardize run telemetry schema:
  - provider, run status, timing, token usage, cache stats, doc/chunk counters
- Freeze minimal contract for downstream UI:
  - lifecycle status
  - progress/report fields
  - deterministic behavior guarantees

## Execution Order
1. Canonical path enforcement
2. CLI guardrails
3. Run report contract
4. Chunking quality upgrades
5. Observability schema alignment
6. Contract freeze and docs update

## Risks
- Legacy paths may still be used in hidden workflows.
- Provider token fields vary and need normalization.
- Cache/report changes can impact existing scripts if not backward-compatible.

## Acceptance Criteria
- CLI supports `--require-service`, `--dry-run`, `--report-path`.
- Translation execution uses canonical provider pipeline.
- Report JSON is emitted deterministically on success/failure.
- Chunking is configurable with safe defaults and deterministic assembly.
- Contract is documented and ready for UI integration.
