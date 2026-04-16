"""Open files or reveal paths in the local OS (desktop app mode)."""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path


def open_file(path: str) -> tuple[bool, str]:
    """Launch the default application for *path* (must be a file)."""
    p = Path(path)
    if not p.is_file():
        return False, "File not found."
    try:
        if platform.system() == "Windows":
            os.startfile(str(p))  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(p)], check=False)
        else:
            subprocess.run(["xdg-open", str(p)], check=False)
    except OSError as exc:
        return False, str(exc)
    return True, "Opened file."


def reveal_in_file_manager(path: str) -> tuple[bool, str]:
    """Open a folder window; if *path* is a file, select it when supported."""
    p = Path(path)
    if not p.exists():
        return False, "Path not found."
    try:
        if platform.system() == "Windows":
            if p.is_file():
                subprocess.run(["explorer", "/select,", str(p.resolve())], check=False)
            else:
                os.startfile(str(p))  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.run(["open", "-R", str(p)] if p.is_file() else ["open", str(p)], check=False)
        else:
            folder = str(p.parent if p.is_file() else p)
            subprocess.run(["xdg-open", folder], check=False)
    except OSError as exc:
        return False, str(exc)
    return True, "Opened file location."
