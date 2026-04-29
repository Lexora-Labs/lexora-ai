# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the Lexora AI desktop app (Windows, one-folder).

Why one-folder (onedir) instead of onefile?
    A PyInstaller onefile EXE self-extracts into ``%TEMP%`` at every launch.
    With Flet 0.21 on Windows this is the #1 reason end users see
    "missing DLL / side-by-side" errors or a silent failure:
      - Antivirus / SmartScreen blocks extraction.
      - Microsoft VC++ runtime is loaded from the temp dir and occasionally
        mismatches what Python 3.12 expects.
      - Flet's ``fletd`` / ``flet.exe`` helpers run from the temp dir and
        lose their data-file relationships.
    Shipping a real folder (``dist\\LexoraAI\\`` containing
    ``LexoraAI.exe`` + ``_internal\\*``) is the recommended PyInstaller
    mode for MSI distribution and completely eliminates that class of
    failure.

Why a spec file instead of ``flet pack``?
    ``flet pack`` does not expose enough hooks to reliably collect:
      - Flet's native runtime binaries (``flet.exe`` / ``fletd`` in ``flet/bin``)
      - Every ``lexora.*`` submodule (providers are imported eagerly, but
        we want a belt-and-braces collect so future dynamic imports don't
        silently break the frozen app)
      - Data/metadata files shipped inside our Python dependencies
        (``cryptography`` native bindings, ``azure.ai.inference`` schemas,
        ``google.genai`` protos, ``openai`` tiktoken bits, ``ebooklib`` /
        ``mobi`` XML templates, etc.)
"""

from pathlib import Path

from PyInstaller.utils.hooks import (
    collect_all,
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

block_cipher = None


# Packages whose absence in the frozen app would cause a runtime
# ModuleNotFoundError that the user CANNOT recover from. We refuse to build
# without them - silent fallback (the previous behaviour) is what shipped a
# broken installer that crashed with "No module named 'cryptography'".
_CRITICAL_PACKAGES = {"flet", "lexora", "cryptography"}

# --- Project layout ---------------------------------------------------------
# The spec is invoked from the repo root in CI (``pyinstaller packaging/windows/lexora_ai.spec``).
REPO_ROOT = Path.cwd()
ENTRY_SCRIPT = str(REPO_ROOT / "src" / "lexora" / "ui" / "main.py")
ICON_PATH = str(REPO_ROOT / "lexora-ai-icon.ico")

# --- Data / binaries / hidden imports ---------------------------------------
datas = [
    # Icon shipped at the bundle root so runtime_paths.py can find it via _MEIPASS.
    (str(REPO_ROOT / "lexora-ai-icon.ico"), "."),
    # Assets directory (branding SVGs, etc.) served by flet as assets_dir.
    (str(REPO_ROOT / "assets"), "assets"),
]
binaries = []
hiddenimports = []


def _collect(pkg_name: str) -> None:
    """Merge collect_all() output into module-level lists.

    Critical packages (see ``_CRITICAL_PACKAGES``) MUST be bundled. If
    ``collect_all`` errors for one of those packages we abort the build
    instead of producing an installer that will crash at runtime with
    ``ModuleNotFoundError``.
    """
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg_name)
    except Exception as exc:  # pragma: no cover - build-time only
        msg = f"[lexora_ai.spec] collect_all({pkg_name!r}) failed: {exc}"
        if pkg_name in _CRITICAL_PACKAGES:
            raise SystemExit(msg)
        print(msg + " (non-critical, skipping)")
        return
    datas.extend(pkg_datas)
    binaries.extend(pkg_binaries)
    hiddenimports.extend(pkg_hidden)


# Flet native runtime: this is the single biggest reason a frozen flet app
# fails to launch - the flet.exe helper must be bundled with its data files.
_collect("flet")

# Our own package - covers every lexora submodule including the provider
# subpackage, logging framework, runtime_paths, etc.
_collect("lexora")

# --- cryptography: extra hardening -----------------------------------------
# ``cryptography`` ships as a Rust-based wheel with native bindings under
# ``cryptography.hazmat.bindings._rust``. PyInstaller's ``collect_all`` can
# miss the submodule import graph (it walks the pure-Python tree only),
# leaving the frozen app to crash with
# ``ModuleNotFoundError: No module named 'cryptography'`` the first time
# ``cryptography.fernet`` is imported. We therefore:
#   1. collect_all to grab everything it CAN see,
#   2. explicitly add every submodule via ``collect_submodules`` so dynamic
#      ``__import__`` calls inside the package resolve at runtime,
#   3. add the native binaries via ``collect_dynamic_libs``,
#   4. copy the package's dist-info / METADATA so any
#      ``importlib.metadata.version("cryptography")`` calls succeed.
_collect("cryptography")
hiddenimports.extend(collect_submodules("cryptography"))
binaries.extend(collect_dynamic_libs("cryptography"))
try:
    datas.extend(copy_metadata("cryptography"))
except Exception as exc:  # pragma: no cover
    print(f"[lexora_ai.spec] copy_metadata('cryptography') skipped: {exc}")

# Crypto / providers / readers - these ship native libs or data files that
# PyInstaller's static analysis regularly misses.
for _pkg in (
    "openai",
    "azure.ai.inference",
    "google.genai",
    "google.generativeai",
    "anthropic",
    "httpx",
    "httpcore",
    "ebooklib",
    "mobi",
    "docx",
    "bs4",
    "lxml",
    "dotenv",
):
    _collect(_pkg)


# --- Analysis / build graph -------------------------------------------------
a = Analysis(
    [ENTRY_SCRIPT],
    pathex=[str(REPO_ROOT / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Onedir build: EXE is the launcher, COLLECT gathers binaries/data into the
# ``dist/LexoraAI/`` folder (LexoraAI.exe + _internal/).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LexoraAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON_PATH,
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LexoraAI",
)
