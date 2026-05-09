# Changelog

All notable changes to Lexora AI are documented here.

## [v0.2.4] - 2026-05-09

### Bug Fixes

- **Desktop window/taskbar icon stays the default Flet icon (LAI-B-004 follow-up):** Flet 0.21.x's bundled Flutter client did not wire `windowIcon` into the Page control, so `page.window.icon` and every Python-side workaround were silently ignored at runtime. Bumped `flet` to **0.23.2** (`requirements.txt`) so `page.window.icon` reaches the native window, and the bundled `lexora-ai-icon.ico` now replaces the default Flet icon in the Windows title bar, taskbar, and Alt+Tab thumbnail in dev (`python run_ui.py --no-browser`) without needing a `flet pack` build.
- **Branding code duplication:** Centralised desktop chrome wiring in new `src/lexora/ui/desktop_branding.py::apply_desktop_branding`. `run_ui.py` and `src/lexora/ui/main.py` now call the shared helper, eliminating two divergent copies of the icon resolution logic.

### Documentation

- **Vietnamese README (`README.vi.md`):** New top-level Vietnamese guide for Windows installation (ZIP and MSI from GitHub Releases, SmartScreen guidance, post-install steps, source build) with a Settings screenshot in Vietnamese.
- **Vietnamese provider/API key guide (`docs/cau-hinh-api-key.vi.md`):** Translated, step-by-step Vietnamese version of `docs/provider-api-key-guide.md` covering OpenAI, Azure OpenAI, Azure AI Foundry, Gemini, Anthropic, and Qwen, plus a combined `.env` template and quick CLI validation snippets.
- **Cross-links:** Added pointers from the English `README.md` and `docs/provider-api-key-guide.md` to the Vietnamese counterparts.

### Internal

- **Spec/docs comment cleanup:** Reworded the onefile vs onedir rationale in `packaging/windows/lexora_ai.spec` and `docs/windows-build-and-packaging.md` to attribute the failure mode to PyInstaller onefile + Python 3.12 on Windows rather than to a specific Flet minor version.

---

## [v0.2.3] - 2026-05-05

### Bug Fixes

- **MSI shortcut placement regression guard (LAI-B-013):** `packaging/windows/Product.wxs` was temporarily reverted to `CommonProgramsFolder` / `CommonDesktopFolder` during ICE cleanup, which made shortcuts land at `D:\Lexora Labs\Lexora AI\` when the MSI was launched from a non-system drive. Restored `ProgramMenuFolder` / `DesktopFolder` (auto-redirected to All Users by `ALLUSERS=1`) and added an explicit regression-guard comment. Documented in `docs/windows-build-and-packaging.md` §7.2.
- **MSI link errors (LGHT0094 / CNDL0035 / CNDL0004):** Reauthored shortcut components to compile cleanly with WiX 3: `Target="[#LexoraAILauncherExe]"`, `Advertise="no"`, HKLM `RegistryValue` KeyPath. Heat output is post-processed by the new `packaging/windows/wix-patch-harvested.ps1` to assign the stable launcher `File` id. `light.exe` runs with `-sval` to bypass ICE38/ICE43/ICE57 (HKLM KeyPath + all-users shortcuts is an intentional trade-off; HKCU broke per-machine installs).

### Documentation

- **README:** New **Context** section for the Translate tab (Tone / Domain / Custom instruction with allowed values, ~8 KB cap, EN/VI labels, Legal/Medical disclaimer). New **CLI Context flags** section with examples for `--tone`, `--domain`, `--instruction`, `--instruction-file`. Roadmap updated: split context-presets follow-up (LAI-T-060, deferred post-v1) from the still-pending glossary path.
- **`docs/todo-list.md`:** LAI-B-013 row records the 2026-05-05 regression and re-fix.

---

## [v0.2.2] - 2026-05-05

### Bug Fixes

- **MSI shortcuts (LAI-B-013):** Windows installer now creates Start Menu and optional Desktop shortcuts under the correct all-users locations (`ProgramMenuFolder` / `DesktopFolder`) regardless of which drive the MSI is run from. Previously, `CommonProgramsFolder` resolved to the install media drive (e.g. `D:\`) instead of `%ProgramData%`, so shortcuts were silently dropped.
- **MSI writable output paths (LAI-B-012):** Default translate output now writes to `user_data_dir()/library` (e.g. `%LOCALAPPDATA%\Lexora Labs\Lexora AI\library`) instead of a path relative to the Program Files install directory. Relative path overrides supplied via the UI are also remapped to the writable location; a safe fallback is used when the target directory cannot be created.
- **UI cache path normalization (LAI-B-014):** Settings UI coerces legacy relative cache paths (e.g. `.lexora/translation_cache.jsonl`) to the user-writable default under `user_data_dir()`, preventing `WinError 5` access-denied errors after MSI installation.
- **EPUB CSS preservation (LAI-B-003):** Translated EPUB chapters now retain the original `<head>` content (stylesheet links, meta tags, charset declarations) merged with the translated `<body>` and localized `<title>`, so output formatting and styling match the source book.

### Features and Improvements

- **Structured EPUB batch on by default:** `--structured-epub-batch` is now the default translation mode for EPUB files. Opt out with `--no-structured-epub-batch`. The `Translator.translate_file` API defaults are aligned with the CLI.
- **Startup loading overlay:** Desktop app shows a localized splash screen while the jobs database and screens initialize, preventing a blank-window appearance on first launch or relaunch.
- **Async session handler:** `main` and `attach_lexora_shell` are now fully `async` with `await` bootstrap instead of `page.run_task`, eliminating cross-thread races that could leave the splash stuck.
- **SQLite connection timeout:** `jobs.sqlite3` opens with `timeout=30.0` to reduce contention when a second app instance briefly holds the database lock.

### CI

- **Windows:** `MSI_PRODUCT_VERSION` is now derived from the GitHub release tag (WiX four-part `n.n.n.n` format).
- **macOS:** `--product-version` is passed to `flet pack` from the tag-derived semver.
- **Manual release trigger:** The desktop release workflow now accepts a `workflow_dispatch` with a `version` input (e.g. `v0.2.2`) that creates and pushes the release tag, then builds and publishes the GitHub release automatically.

### Tests

- `tests/test_translate_output_paths.py` — output path resolution under MSI-style environments.
- `tests/test_ui_cache_path_normalization.py` — legacy cache path coercion in the Settings UI.

---

## [v0.2.1.1] - 2026-04-29

### Bug Fixes

- **Windows packaging:** Moved to PyInstaller onedir build + WiX MSI harvesting (`heat`/`candle`/`light`) for reliable and consistent artifact creation in CI.
- **MSI shortcut components (LAI-B-009):** Fixed shortcut components using HKCU KeyPath under a per-machine MSI install; switched to HKLM KeyPath and `CommonDesktopFolder` for all-users desktop shortcuts.
- **Frozen app missing `cryptography` (LAI-B-008):** Hardened `packaging/windows/lexora_ai.spec` to explicitly include `cryptography` submodules, dynamic libraries, and dist-info metadata so the frozen EXE no longer crashes at startup with `ModuleNotFoundError`.
- **App data in Program Files (LAI-B-007):** Added `src/lexora/runtime_paths.py::user_data_dir()` with resolution order `LEXORA_DATA_DIR` → existing `./.lexora/` (legacy) → `%LOCALAPPDATA%\Lexora Labs\Lexora AI`. Updated secrets, jobs, and cache defaults to use writable paths.
- **Settings: long endpoint URLs hidden (LAI-B-010):** Endpoint-style fields switched to `multiline=True, min_lines=1, max_lines=1`; forced small height removed so long unbroken URLs are visible and editable.
- **Settings: KEY fields blank/reveal wrong value (LAI-B-011):** API key fields use the same multiline fix; eye-toggle loads the actual stored key via `get_secret_first`.
- **EPUB head preservation:** Original XHTML `<head>` (stylesheets, meta, charset) restored after translation; whitespace around inline tags (`<a>`, `<em>`, `<code>`) preserved.

### Features and Improvements

- Added provider-delete confirmation dialog in Settings.
- Added local Windows packaging guide and script (`packaging/windows/build-local.ps1`, `docs/windows-build-and-packaging.md`).

---

## [v0.1.1] - 2026-04-17

Initial public release.

- **Desktop app (Flet UI):** Translate, Jobs, Settings, and About screens with dark/light/system theme support.
- **CLI (`lexora translate`):** Scriptable EPUB translation with structured JSON batch mode for OpenAI, Azure Foundry, and Gemini providers.
- **Jobs lifecycle:** Persist job state to local SQLite; queue, history, filters, run log, cancel/retry/delete, and open output.
- **Logging framework:** File sinks, structured events, tokenized file naming, and sink routing.
- **EPUB pipeline:** Sanitization, inline tag preservation, and provider-key guide.
- **GitHub Actions:** Desktop release pipeline shipping Windows MSI + ZIP and macOS ZIP on every `v*` tag.
