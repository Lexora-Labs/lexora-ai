# Windows — Local Build & Packaging Guide

This guide explains how to build the Lexora AI Windows desktop app and its
MSI installer on your own machine, so you can verify a release end-to-end
before pushing a tag and kicking off the CI workflow at
[`.github/workflows/desktop-release.yml`](../.github/workflows/desktop-release.yml).

The local build uses the exact same tools, spec file and WiX sources as CI,
so "it works locally" translates directly to "it will work in CI".

---

## 1. Prerequisites (one-time)

Install these once on your Windows dev machine:

| Tool | Version | Why |
| --- | --- | --- |
| **Python** | 3.12.x | Matches CI. Use the same minor version to avoid ABI surprises with `cryptography` / `pydantic` native wheels. |
| **PowerShell** | 5.1 or 7+ | The local build script is `build-local.ps1`. |
| **Git** | any | Clone / branch the repo. |
| **WiX Toolset** | 3.14.x | Provides `candle.exe`, `light.exe`, `heat.exe` used to build the MSI. |

### Install WiX 3.14

Easiest route (Chocolatey):

```powershell
choco install wixtoolset --version=3.14.1 -y
```

Or download the `wix314.exe` installer from <https://wixtoolset.org/releases/>.

After install, close and reopen your PowerShell so `PATH` picks up the new tools.
The binaries live at:

```
C:\Program Files (x86)\WiX Toolset v3.14\bin\{candle,light,heat}.exe
```

The build script auto-discovers this path — you don't need to edit anything.

---

## 2. What the build produces

Running `build-local.ps1` produces three artifacts in the repo root:

| File | Type | Use for |
| --- | --- | --- |
| `dist\LexoraAI\LexoraAI.exe` | Portable onedir EXE | Fastest smoke test. No install needed. |
| `LexoraAI-windows-amd64.zip` | Portable archive | What end users download from GitHub Releases as the "portable" option. |
| `LexoraAI-windows-amd64.msi` | Installer | What end users download and install. Offers Start Menu / Desktop shortcut options. |

### Why onedir (folder) instead of onefile?

A PyInstaller **onefile** EXE self-extracts into `%TEMP%` at every launch.
With Flet 0.21 + Python 3.12 on Windows this is the #1 cause of end-user
"missing DLL / side-by-side configuration" errors and silent failures:

- Antivirus / SmartScreen blocks or throttles the extraction.
- VC++ runtime loads from a temp dir and occasionally mismatches.
- Flet's `fletd` / `flet.exe` helpers lose their data-file relationships.

Shipping a real folder (`dist\LexoraAI\` with `LexoraAI.exe` + `_internal\`)
is the PyInstaller-recommended mode for MSI distribution and completely
removes that class of failure.

---

## 3. Quick start

From the repo root:

```powershell
cd <path>\lexora-ai
.\packaging\windows\build-local.ps1
```

If PowerShell blocks the script due to execution policy:

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\windows\build-local.ps1
```

On the first run the script will:

1. Create `.\.venv` (if missing).
2. `pip install -r requirements.txt`, `pip install .` and the PyInstaller /
   Pillow toolchain.
3. Run `pyinstaller packaging\windows\lexora_ai.spec` → `dist\LexoraAI\`.
4. Zip the `dist\LexoraAI` folder → `LexoraAI-windows-amd64.zip`.
5. Harvest the folder with `heat.exe`, compile with `candle.exe`, link with
   `light.exe` → `LexoraAI-windows-amd64.msi`.

On a typical dev machine the full run is ~2–4 minutes. Subsequent runs with
`-SkipInstall` are closer to ~30–60s.

---

## 4. Script options

```powershell
.\packaging\windows\build-local.ps1 [-Version <n.n.n.n>] [-SkipInstall] [-SkipMsi]
```

| Option | When to use |
| --- | --- |
| `-Version 0.2.1.0` | Set the MSI `ProductVersion`. Must be `n.n.n.n`. Defaults to `0.0.0.0` for local builds. |
| `-SkipInstall` | Skip the `pip install` steps. Use after the first successful build to iterate faster. |
| `-SkipMsi` | Build only the EXE + ZIP; skip heat/candle/light. Handy when you're still debugging the frozen EXE itself. |

Examples:

```powershell
# Rebuild just the EXE + ZIP (fast), don't touch WiX
.\packaging\windows\build-local.ps1 -SkipInstall -SkipMsi

# Build an installer with a proper version for a release dry-run
.\packaging\windows\build-local.ps1 -Version 0.2.1.0
```

---

## 5. Test matrix

After the build finishes, test in this order. Each step isolates a different
class of failure.

### 5.1 Portable EXE (smoke test)

```powershell
.\dist\LexoraAI\LexoraAI.exe
```

Expected: the Lexora AI window opens.

If this fails, the problem is in the **PyInstaller spec**, not WiX. See
[Section 7 — Troubleshooting](#7-troubleshooting).

### 5.2 Portable ZIP

Extract `LexoraAI-windows-amd64.zip` into, say, `C:\Temp\LexoraTest\`
and double-click `LexoraTest\LexoraAI\LexoraAI.exe`.

Expected: same as 5.1. This verifies there are no absolute-path assumptions
baked into the bundle.

### 5.3 MSI install

Install with verbose logging so you can diagnose any surprises:

```powershell
msiexec /i LexoraAI-windows-amd64.msi /l*v install.log
```

On the **"Custom Setup"** page, expand **Lexora AI** — you should see:

- **Start menu shortcut** — "Will be installed on local hard drive" (checked by default)
- **Desktop shortcut** — "Will be installed on local hard drive" (checked by default)

Leave both checked and complete the install.

Verify afterwards:

```powershell
# Installed EXE (per-machine, Program Files)
Test-Path "$env:ProgramFiles\Lexora Labs\Lexora AI\LexoraAI.exe"

# All-users desktop shortcut
Test-Path "$env:PUBLIC\Desktop\Lexora AI.lnk"

# All-users Start Menu shortcut
Test-Path "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Lexora AI\Lexora AI.lnk"
```

All three should print `True`. Click each shortcut — the app should launch.

> **Note.** This is a **per-machine** install (`InstallScope="perMachine"`,
> `ALLUSERS=1`), so shortcuts land in the All Users profile, not your
> personal `Desktop\`. If you're looking on `C:\Users\<you>\Desktop`,
> you won't see them — check `C:\Users\Public\Desktop` instead.

### 5.4 Uninstall

```powershell
msiexec /x LexoraAI-windows-amd64.msi /l*v uninstall.log
```

Then re-run the three `Test-Path` checks above. All should now print
`False`. Also confirm Apps & Features no longer lists "Lexora AI".

---

## 6. Iteration loop

Typical workflows:

- **Iterating on UI / app code** → rebuild everything (onedir EXE must be
  refreshed) but skip dependency install:
  ```powershell
  .\packaging\windows\build-local.ps1 -SkipInstall
  ```

- **Iterating only on `Product.wxs`** → skip the slow PyInstaller step
  entirely by reusing the existing `dist\LexoraAI\` folder. The script
  doesn't support this out of the box; run the MSI commands manually:

  ```powershell
  $wixBin = "C:\Program Files (x86)\WiX Toolset v3.14\bin"
  $out    = "$env:TEMP\lexora-wixout"
  Remove-Item $out -Recurse -Force -ErrorAction SilentlyContinue
  New-Item -ItemType Directory -Force $out | Out-Null

  $harvest = (Resolve-Path "dist\LexoraAI").Path

  & "$wixBin\heat.exe" dir $harvest `
    -cg LexoraComponents -dr APPLICATIONFOLDER `
    -srd -sreg -scom -sfrag -gg -ke `
    -var "var.HarvestSource" `
    -out "$out\LexoraComponents.wxs"

  & "$wixBin\candle.exe" -arch x64 `
    "-dHarvestSource=$harvest" "-dSourceDir=$harvest" "-dProductVersion=0.0.0.0" `
    -out "$out\Product.wixobj" "packaging\windows\Product.wxs"

  & "$wixBin\candle.exe" -arch x64 `
    "-dHarvestSource=$harvest" `
    -out "$out\LexoraComponents.wixobj" "$out\LexoraComponents.wxs"

  & "$wixBin\light.exe" -ext WixUIExtension `
    -out "LexoraAI-windows-amd64.msi" `
    "$out\Product.wixobj" "$out\LexoraComponents.wixobj"
  ```

---

## 7. Troubleshooting

### 7.1 `LexoraAI.exe` won't start (missing DLL, side-by-side, silent crash)

1. **Open a console build** to see the actual Python traceback. Temporarily
   edit `packaging\windows\lexora_ai.spec` and change:
   ```python
   console=False
   ```
   to:
   ```python
   console=True
   ```
   Rebuild (`-SkipInstall`) and re-run `.\dist\LexoraAI\LexoraAI.exe`. A
   console window will stay open with the error. **Revert `console=True`
   before committing.**

2. **Check for antivirus interference.** Windows Defender / third-party AV
   sometimes flags or quarantines freshly built PyInstaller EXEs. Exclude
   the `dist\` folder during testing.

3. **Confirm the `_internal\` folder is next to the EXE.** In onedir mode,
   `LexoraAI.exe` must sit beside `_internal\` — if you copy only the EXE,
   nothing will work.

### 7.2 MSI installs but shortcuts don't appear

The installer log is the single source of truth:

```powershell
Select-String -Path install.log -Pattern "DesktopShortcut|StartMenuShortcut" -SimpleMatch
```

Look for lines like:

```
MSI (s) ... : Component: DesktopShortcut; ... Installed: Absent; Request: Local; Action: Local
```

What to check:

- `Request: Local` and `Action: Local` → the component **will** be installed.
  If the `.lnk` file still doesn't appear afterwards, look at the
  `CreateShortcuts:` line in the log for the resolved target path.
- `Request: Null` or `Action: Null` → Windows Installer dropped the
  component. The usual culprit is a per-user `KeyPath` (HKCU) inside a
  per-machine install. Our `Product.wxs` uses HKLM — if you've edited it,
  make sure the `RegistryValue` under each shortcut component keeps
  `Root="HKLM"`.

### 7.3 heat.exe produces an empty `LexoraComponents.wxs`

Means the `dist\LexoraAI\` folder is empty or missing. Re-run the build
without `-SkipMsi` to regenerate the onedir output first.

### 7.4 `light.exe : error LGHT0103`

Usually a missing variable. Make sure both candle invocations receive
`-dHarvestSource=<dist\LexoraAI path>`, and that the `Product.wxs` candle
call also gets `-dSourceDir=<same path>` and `-dProductVersion=<n.n.n.n>`.

### 7.5 Re-install fails with "A newer version is already installed"

`Product.wxs` declares a `MajorUpgrade` rule: installing an older
`ProductVersion` over a newer one is blocked by design. Uninstall first:

```powershell
msiexec /x LexoraAI-windows-amd64.msi
```

Or bump `-Version` to something higher than what's installed.

---

## 8. Where the installed app stores data

Once installed via the MSI, runtime state (encrypted secrets, jobs DB,
translation cache) does **not** live under `Program Files` — that folder
is read-only for non-admin users. Lexora resolves writes to a
per-user, OS-appropriate directory instead:

| OS | Default data directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%\Lexora Labs\Lexora AI\` |
| macOS | `~/Library/Application Support/Lexora AI/` |
| Linux | `$XDG_DATA_HOME/lexora-ai` (or `~/.local/share/lexora-ai`) |

Resolution order (see `src/lexora/runtime_paths.py::user_data_dir`):

1. `LEXORA_DATA_DIR` env var (explicit override) — highest priority.
2. `./.lexora/` next to the current working directory **if it already
   exists** — preserves the legacy CLI / dev-mode layout.
3. The OS-specific directory above (auto-created).

This is why a freshly-installed MSI lands writes in
`%LOCALAPPDATA%\Lexora Labs\Lexora AI\` while running `python -m lexora.cli`
from a project folder that already has `.lexora/` keeps using the project
folder.

To **wipe local app data** during testing:

```powershell
Remove-Item "$env:LOCALAPPDATA\Lexora Labs\Lexora AI" -Recurse -Force
```

To **point the app elsewhere** for one run (or via a desktop shortcut
"Properties \u2192 Target" tweak):

```powershell
$env:LEXORA_DATA_DIR = "D:\my-lexora-data"
& "$env:ProgramFiles\Lexora Labs\Lexora AI\LexoraAI.exe"
```

> The MSI uninstaller intentionally does NOT delete this folder \u2014 your
> API keys and translation cache survive uninstalls and upgrades, mirroring
> conventional Windows app behaviour. Remove the folder manually if you
> want a true clean slate.

---

## 9. When you're ready to release

Once the local MSI installs cleanly and both shortcuts work, push a tag:

```powershell
git tag v0.2.1
git push origin v0.2.1
```

The `Desktop release` workflow will run, produce the exact same artifacts
(using the same spec + WiX sources you just tested), and publish them to
the GitHub Release for the tag.

---

## Related files

- [`packaging/windows/build-local.ps1`](../packaging/windows/build-local.ps1) — the local build script.
- [`packaging/windows/lexora_ai.spec`](../packaging/windows/lexora_ai.spec) — PyInstaller onedir spec.
- [`packaging/windows/Product.wxs`](../packaging/windows/Product.wxs) — WiX installer source.
- [`.github/workflows/desktop-release.yml`](../.github/workflows/desktop-release.yml) — the CI workflow that mirrors this script.
- [`src/lexora/runtime_paths.py`](../src/lexora/runtime_paths.py) — `user_data_dir()` / `lexora_data_file()` helpers used by `secrets.py`, `app_shell.py`, and `cli.py` to choose a writable per-user directory.
