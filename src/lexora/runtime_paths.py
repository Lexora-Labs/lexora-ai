"""Resolve Lexora-AI repository, bundle root, and writable user-data paths.

Two responsibilities:

1. ``lexora_repo_root``: locate the bundled assets dir for both source
   checkouts and frozen PyInstaller / ``flet pack`` builds.

2. ``user_data_dir`` / ``lexora_data_file``: locate a *writable* per-user
   directory for Lexora's runtime state (encrypted secrets, jobs DB,
   translation cache).

   This matters for the MSI installer: when the app is installed under
   ``C:\\Program Files\\Lexora Labs\\Lexora AI\\`` Windows launches it with
   that directory as cwd, but Program Files is read-only for non-admin
   users. Defaulting writes to a relative ``.lexora/`` path therefore
   crashes with ``[WinError 5] Access is denied``. We resolve writes to
   ``%LOCALAPPDATA%\\Lexora Labs\\Lexora AI`` instead, which every
   Windows user can write to and which survives MSI upgrades/uninstalls
   (data is intentionally NOT removed when the app is uninstalled, mirroring
   conventional Windows app behaviour).

Resolution priority for ``lexora_data_file``:

* ``$LEXORA_DATA_DIR``  - explicit override, highest priority
* ``./.lexora/``        - legacy in-CWD folder, *only if it already exists*
* OS-specific user-data dir (auto-created)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_PUBLISHER = "Lexora Labs"
APP_NAME = "Lexora AI"


def lexora_repo_root(*, anchor_file: Path | None = None) -> Path:
    """Return repo root in development or the frozen bundle root when packaged.

    In a ``flet pack`` / PyInstaller build, ship ``assets/`` and ``lexora-ai-icon.ico``
    at the bundle root (``sys._MEIPASS`` for one-file) via ``--add-data``.
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent

    start = anchor_file.resolve() if anchor_file is not None else Path(__file__).resolve()
    for ancestor in [start] + list(start.parents):
        if (ancestor / "README.md").is_file() and (ancestor / "requirements.txt").is_file():
            return ancestor
    # Fallback: lexora/ui/main.py -> repo is parents[3]
    return Path(__file__).resolve().parents[2]


def _platform_user_data_dir() -> Path:
    """Return the OS-appropriate user-data directory for this app.

    Windows : ``%LOCALAPPDATA%\\Lexora Labs\\Lexora AI``
              (falls back to ``%APPDATA%`` then ``~`` if not set)
    macOS   : ``~/Library/Application Support/Lexora AI``
    Linux/* : ``$XDG_DATA_HOME/lexora-ai`` or ``~/.local/share/lexora-ai``
    """
    if sys.platform == "win32":
        base = (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or str(Path.home())
        )
        return Path(base) / APP_PUBLISHER / APP_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    # Linux / *nix - follow XDG Base Directory spec.
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "lexora-ai"
    return Path.home() / ".local" / "share" / "lexora-ai"


def user_data_dir(*, ensure_exists: bool = True) -> Path:
    """Return the writable user-data directory for Lexora-AI.

    Resolution order:
      1. ``$LEXORA_DATA_DIR``   - explicit override
      2. ``./.lexora/``         - legacy in-CWD folder, *only if it already exists*
      3. OS-specific user-data dir (auto-created)

    The legacy step (2) preserves the existing behaviour for developers and
    CLI users who have built up a ``.lexora`` folder next to their ebooks.
    A fresh install (e.g. the MSI) skips step 2 and lands on step 3, which
    is always writable.
    """
    override = (os.environ.get("LEXORA_DATA_DIR") or "").strip()
    if override:
        path = Path(override).expanduser()
    else:
        legacy = Path.cwd() / ".lexora"
        if legacy.is_dir():
            path = legacy
        else:
            path = _platform_user_data_dir()

    if ensure_exists:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            # If the chosen path is somehow not writable (e.g. user pointed
            # LEXORA_DATA_DIR at a read-only location), fall back to the
            # platform default rather than crashing.
            fallback = _platform_user_data_dir()
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
    return path


def lexora_data_file(*relative_parts: str) -> Path:
    """Return a path under :func:`user_data_dir` and ensure parent exists."""
    target = user_data_dir().joinpath(*relative_parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
